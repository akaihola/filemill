{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [ gcc pkg-config python3 webkitgtk_4_1 gtk3 xorg-server ];
}
