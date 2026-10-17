{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [ gcc pkg-config python3 webkitgtk_4_1 gtk3 xorg-server ];
  # Playwright's greenlet wheel, imported by static/test-ui.py, needs libstdc++.
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ];
}
