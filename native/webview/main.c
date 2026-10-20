#define _GNU_SOURCE
#include <webkit2/webkit2.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdint.h>
#include <sys/stat.h>
#include <unistd.h>
#include "build/resource.h"

static int root_fd = -1;
static char *root_name;
static GPtrArray *locations;
static int location_index = -1;
static gboolean automation;

/* Walk descriptors, never string prefixes: no symlink can escape the root. */
static int open_relative(const char *path, int flags) {
    if (!path || path[0] == '/') { errno = EINVAL; return -1; }
    int fd = openat(root_fd, ".", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
    gchar **parts = g_strsplit(path, "/", -1);
    for (int i = 0; parts[i]; i++) {
        if (!*parts[i]) continue;
        if (!strcmp(parts[i], ".") || !strcmp(parts[i], "..")) {
            close(fd); fd = -1; errno = EACCES; break;
        }
        int next = openat(fd, parts[i], O_CLOEXEC | O_NOFOLLOW |
                          (parts[i + 1] ? O_RDONLY | O_DIRECTORY : flags));
        int error = errno;
        close(fd); fd = next; errno = error;
        if (fd < 0) break;
    }
    g_strfreev(parts);
    return fd;
}
static char *string_property(JSCValue *value, const char *name) {
    JSCValue *property = jsc_value_object_get_property(value, name);
    char *text = jsc_value_is_string(property) ? jsc_value_to_string(property) : NULL;
    g_object_unref(property);
    return text;
}
static void set_string(JSCValue *object, const char *name, const char *text) {
    JSCValue *value = jsc_value_new_string(jsc_value_get_context(object), text);
    jsc_value_object_set_property(object, name, value);
    g_object_unref(value);
}
static void set_number(JSCValue *object, const char *name, double number) {
    JSCValue *value = jsc_value_new_number(jsc_value_get_context(object), number);
    jsc_value_object_set_property(object, name, value);
    g_object_unref(value);
}
/* Include inode identity and nanosecond times; replacing equal-size bytes is
 * still a new revision. Symlinks remain forbidden by open_relative(). */
static char *file_revision(const struct stat *info) {
    return g_strdup_printf("%ju-%ju-%ju-%jd-%ld-%jd-%ld",
        (uintmax_t)info->st_dev, (uintmax_t)info->st_ino, (uintmax_t)info->st_size,
        (intmax_t)info->st_mtim.tv_sec, info->st_mtim.tv_nsec,
        (intmax_t)info->st_ctim.tv_sec, info->st_ctim.tv_nsec);
}

static gboolean pick_root(void) {
    GtkWidget *dialog = gtk_file_chooser_dialog_new("Open Folder", NULL,
        GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER, "Cancel", GTK_RESPONSE_CANCEL,
        "Open", GTK_RESPONSE_ACCEPT, NULL);
    gboolean changed = FALSE;
    if (gtk_dialog_run(GTK_DIALOG(dialog)) == GTK_RESPONSE_ACCEPT) {
        char *directory = gtk_file_chooser_get_filename(GTK_FILE_CHOOSER(dialog));
        int fd = open(directory, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
        if (fd >= 0) {
            if (root_fd >= 0) close(root_fd);
            root_fd = fd;
            g_free(root_name); root_name = g_path_get_basename(directory);
            if (locations) g_ptr_array_set_size(locations, 0);
            location_index = -1;
            changed = TRUE;
        }
        g_free(directory);
    }
    gtk_widget_destroy(dialog);
    return changed;
}
static gboolean message(WebKitUserContentManager *manager, JSCValue *request,
                        WebKitScriptMessageReply *reply, gpointer data) {
    JSCContext *context = jsc_value_get_context(request);
    JSCValue *result = NULL;
    char *op = string_property(request, "op");
    char *path = string_property(request, "path");
    int fd = -1;
    errno = EINVAL;
    if (!op) goto finish;
    if (!strcmp(op, "pick")) {
        result = jsc_value_new_boolean(context, pick_root());
    } else if (!strcmp(op, "root")) {
        result = jsc_value_new_object(context, NULL, NULL);
        set_string(result, "name", root_name);
    } else if (!strcmp(op, "route")) {
        JSCValue *state = jsc_value_object_get_property(request, "state");
        JSCValue *replace = jsc_value_object_get_property(request, "replace");
        if (jsc_value_is_object(state)) {
            char *json = jsc_value_to_json(state, 0);
            if (jsc_value_to_boolean(replace) && location_index >= 0) {
                g_free(g_ptr_array_index(locations, location_index));
                g_ptr_array_index(locations, location_index) = json;
            } else {
                g_ptr_array_set_size(locations, location_index + 1);
                g_ptr_array_add(locations, json);
                location_index++;
            }
            result = jsc_value_new_null(context);
        }
        g_object_unref(state); g_object_unref(replace);
    } else if (!strcmp(op, "navigate")) {
        JSCValue *delta = jsc_value_object_get_property(request, "delta");
        int step = jsc_value_to_int32(delta);
        g_object_unref(delta);
        if (step != -1 && step != 1) goto finish;
        int next = location_index + step;
        if (next >= 0 && next < (int)locations->len) location_index = next;
        result = location_index < 0 ? jsc_value_new_null(context) :
            jsc_value_new_from_json(context, g_ptr_array_index(locations, location_index));
    } else {
        fd = open_relative(path, !strcmp(op, "write") ? O_WRONLY | O_NONBLOCK : O_RDONLY | O_NONBLOCK);
        if (fd < 0) goto finish;
        struct stat info;
        if (fstat(fd, &info)) goto finish;
        if (!strcmp(op, "list") && S_ISDIR(info.st_mode)) {
            DIR *directory = fdopendir(dup(fd));
            if (!directory) goto finish;
            result = jsc_value_new_array(context, G_TYPE_NONE);
            struct dirent *entry;
            unsigned index = 0;
            while ((entry = readdir(directory))) {
                if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
                struct stat child;
                if (fstatat(fd, entry->d_name, &child, AT_SYMLINK_NOFOLLOW) ||
                    (!S_ISREG(child.st_mode) && !S_ISDIR(child.st_mode))) continue;
                JSCValue *node = jsc_value_new_object(context, NULL, NULL);
                set_string(node, "name", entry->d_name);
                char *rel = *path ? g_strconcat(path, "/", entry->d_name, NULL) : g_strdup(entry->d_name);
                set_string(node, "path", rel); g_free(rel);
                JSCValue *dir = jsc_value_new_boolean(context, S_ISDIR(child.st_mode));
                jsc_value_object_set_property(node, "dir", dir); g_object_unref(dir);
                jsc_value_object_set_property_at_index(result, index++, node); g_object_unref(node);
            }
            closedir(directory);
        } else if (!strcmp(op, "stat")) {
            result = jsc_value_new_object(context, NULL, NULL);
            set_number(result, "size", info.st_size);
            set_number(result, "mod", info.st_mtim.tv_sec * 1000.0 + info.st_mtim.tv_nsec / 1000000.0);
            set_string(result, "type", "");
        } else if (!strcmp(op, "read") && S_ISREG(info.st_mode)) {
            GByteArray *bytes = g_byte_array_new();
            unsigned char buffer[65536];
            ssize_t count;
            while ((count = read(fd, buffer, sizeof(buffer))) > 0) g_byte_array_append(bytes, buffer, count);
            if (count == 0) {
                char *encoded = g_base64_encode(bytes->data, bytes->len);
                struct stat after;
                char *before_revision = file_revision(&info);
                if (!fstat(fd, &after)) {
                    char *revision = file_revision(&after);
                    if (!strcmp(before_revision, revision)) {
                        result = jsc_value_new_object(context, NULL, NULL);
                        set_string(result, "bytes", encoded);
                        set_string(result, "revision", revision);
                    } else errno = ESTALE;
                    g_free(revision);
                }
                g_free(before_revision); g_free(encoded);
            }
            g_byte_array_unref(bytes);
        } else if (!strcmp(op, "write") && S_ISREG(info.st_mode) && *path) {
            char *expected = string_property(request, "revision");
            char *actual = file_revision(&info);
            gboolean matches = expected && !strcmp(expected, actual);
            g_free(expected); g_free(actual);
            if (!matches) { errno = ESTALE; goto finish; }
            JSCValue *value = jsc_value_object_get_property(request, "text");
            if (jsc_value_is_string(value)) {
                GBytes *bytes = jsc_value_to_string_as_bytes(value);
                gsize length;
                const char *text = g_bytes_get_data(bytes, &length);
                char *parent = g_path_get_dirname(path);
                char *name = g_path_get_basename(path);
                int parent_fd = open_relative(!strcmp(parent, ".") ? "" : parent, O_RDONLY | O_DIRECTORY);
                if (parent_fd >= 0) {
                    char *target = g_strdup_printf("/proc/self/fd/%d/%s", parent_fd, name);
                    GError *error = NULL;
                    /* GLib replaces one directory entry: other hard links keep
                     * old bytes. Mode is preserved; ownership and other metadata
                     * follow GLib's replacement contract; preservation is not guaranteed. */
                    struct stat current;
                    char *original_revision = file_revision(&info);
                    char *current_revision = fstatat(parent_fd, name, &current, AT_SYMLINK_NOFOLLOW)
                        ? NULL : file_revision(&current);
                    if (!current_revision || strcmp(original_revision, current_revision)) errno = ESTALE;
                    else if (g_file_set_contents_full(target, text ? text : "", length,
                        G_FILE_SET_CONTENTS_CONSISTENT | G_FILE_SET_CONTENTS_DURABLE,
                        info.st_mode & 0777, &error)) {
                        if (!fstatat(parent_fd, name, &current, AT_SYMLINK_NOFOLLOW)) {
                            char *revision = file_revision(&current);
                            result = jsc_value_new_string(context, revision);
                            g_free(revision);
                        }
                    } else { errno = EIO; g_clear_error(&error); }
                    g_free(original_revision); g_free(current_revision);
                    g_free(target); close(parent_fd);
                }
                g_free(parent); g_free(name);
                g_bytes_unref(bytes);
            }
            g_object_unref(value);
        }
    }
finish:
    if (result) { webkit_script_message_reply_return_value(reply, result); g_object_unref(result); }
    else {
        /* The errno name is the stable part; g_strerror follows the locale. */
        int code = errno;
        const char *name = strerrorname_np(code);
        char *text = g_strdup_printf("%s: %s", name ? name : "EIO", g_strerror(code));
        webkit_script_message_reply_return_error_message(reply, text);
        g_free(text);
    }
    if (fd >= 0) close(fd);
    g_free(op); g_free(path);
    return TRUE;
}
static void resource_request(WebKitURISchemeRequest *request, gpointer data) {
    GInputStream *stream = g_memory_input_stream_new_from_data(resource, sizeof(resource), NULL);
    webkit_uri_scheme_request_finish(request, stream, sizeof(resource), "text/html");
    g_object_unref(stream);
}
static gboolean policy(WebKitWebView *view, WebKitPolicyDecision *decision,
                       WebKitPolicyDecisionType type, gpointer data) {
    if (type == WEBKIT_POLICY_DECISION_TYPE_NAVIGATION_ACTION) {
        const char *uri = webkit_uri_request_get_uri(webkit_navigation_action_get_request(webkit_navigation_policy_decision_get_navigation_action(WEBKIT_NAVIGATION_POLICY_DECISION(decision))));
        if (strcmp(uri, "filemill://app/") && !g_str_has_prefix(uri, "blob:filemill://app/")) {
            webkit_policy_decision_ignore(decision); return TRUE;
        }
    }
    if (type == WEBKIT_POLICY_DECISION_TYPE_NEW_WINDOW_ACTION) {
        webkit_policy_decision_ignore(decision); return TRUE;
    }
    if (type == WEBKIT_POLICY_DECISION_TYPE_RESPONSE &&
        webkit_response_policy_decision_is_main_frame_main_resource(WEBKIT_RESPONSE_POLICY_DECISION(decision))) {
        const char *uri = webkit_uri_request_get_uri(webkit_response_policy_decision_get_request(WEBKIT_RESPONSE_POLICY_DECISION(decision)));
        if (strcmp(uri, "filemill://app/")) {
            webkit_policy_decision_ignore(decision); return TRUE;
        }
    }
    return FALSE;
}
static WebKitWebView *create_view(WebKitAutomationSession *session, gpointer data) {
    WebKitUserContentManager *manager = webkit_user_content_manager_new();
    webkit_user_content_manager_register_script_message_handler_with_reply(manager, "filemill", NULL);
    g_signal_connect(manager, "script-message-with-reply-received::filemill", G_CALLBACK(message), NULL);
    WebKitWebView *view = g_object_new(WEBKIT_TYPE_WEB_VIEW, "web-context", data,
        "user-content-manager", manager, "is-controlled-by-automation", automation, NULL);
    g_object_unref(manager);
    g_signal_connect(view, "decide-policy", G_CALLBACK(policy), NULL);
    GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_default_size(GTK_WINDOW(window), 1500, 900);
    gtk_window_set_title(GTK_WINDOW(window), "Filemill");
    gtk_container_add(GTK_CONTAINER(window), GTK_WIDGET(view));
    if (!automation) g_signal_connect(window, "destroy", G_CALLBACK(gtk_main_quit), NULL);
    gtk_widget_show_all(window);
    webkit_web_view_load_uri(view, "filemill://app/");
    return view;
}
static void started(WebKitWebContext *context, WebKitAutomationSession *session, gpointer data) {
    g_signal_connect(session, "create-web-view", G_CALLBACK(create_view), context);
}
int main(int argc, char **argv) {
    gtk_init(&argc, &argv);
    /* WebKit's overlay scrollbars catch clicks across a 21px band over the
       last row and every row's chevron; classic ones take layout space. */
    g_object_set(gtk_settings_get_default(), "gtk-overlay-scrolling", FALSE, NULL);
    const char *root = g_getenv("FILEMILL_ROOT");
    automation = argc > 1 && !strcmp(argv[1], "--automation");
    if (!automation && argc > 1) root = argv[1];
    if (automation && g_getenv("FILEMILL_TEST_THEME")) g_object_set(gtk_settings_get_default(), "gtk-application-prefer-dark-theme", !strcmp(g_getenv("FILEMILL_TEST_THEME"), "dark"), NULL);
    if (root) {
        root_fd = open(root, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
        if (root_fd < 0) { perror(root); return 1; }
        root_name = g_path_get_basename(root);
    } else if (automation || !pick_root()) return 2;
    locations = g_ptr_array_new_with_free_func(g_free);
    /* Like a fresh browser context, a test session keeps no stored settings. */
    WebKitWebContext *context = automation ? webkit_web_context_new_ephemeral()
                                           : webkit_web_context_get_default();
    webkit_web_context_register_uri_scheme(context, "filemill", resource_request, NULL, NULL);
    webkit_security_manager_register_uri_scheme_as_secure(webkit_web_context_get_security_manager(context), "filemill");
    if (automation) {
        webkit_web_context_set_automation_allowed(context, TRUE);
        g_signal_connect(context, "automation-started", G_CALLBACK(started), NULL);
    } else create_view(NULL, context);
    gtk_main();
    close(root_fd); g_free(root_name); g_ptr_array_unref(locations);
    return 0;
}
