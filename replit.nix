{pkgs}: {
  deps = [
    pkgs.python312Packages.pytest_7
    pkgs.python312Packages.twine
    pkgs.libxcrypt
  ];
}
