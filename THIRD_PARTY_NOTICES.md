# Third-party notices

The MIT license in this repository applies to the project's original code and documentation. Third-party fonts, images, and dependencies retain their own copyrights and terms; they are not relicensed under MIT.

## Bundled fonts

These fonts use the SIL Open Font License 1.1. The full notices and license texts are included alongside the font files in `references/fonts/`.

| Family | Copyright / project | Bundled license |
| --- | --- | --- |
| Inter | Copyright 2016 The Inter Project Authors; [rsms/inter](https://github.com/rsms/inter) | [Inter-OFL.txt](references/fonts/Inter-OFL.txt) |
| IBM Plex Sans | IBM Corp.; [IBM/plex](https://github.com/IBM/plex) | [IBMPlexSans-OFL.txt](references/fonts/IBMPlexSans-OFL.txt) |
| Rajdhani | Copyright 2014 Indian Type Foundry; [Google Fonts distribution](https://github.com/google/fonts/tree/main/ofl/rajdhani) | [Rajdhani-OFL.txt](references/fonts/Rajdhani-OFL.txt) |
| Space Mono | Copyright 2016 The Space Mono Project Authors; [googlefonts/spacemono](https://github.com/googlefonts/spacemono) | [SpaceMono-OFL.txt](references/fonts/SpaceMono-OFL.txt) |

IBM Plex Sans Regular, Medium, and SemiBold were obtained from the official IBM Plex repository's `packages/plex-sans/fonts/complete/ttf/` directory. The other bundled fonts retain their embedded family and copyright metadata.

## Detection and interface images

`references/`, `map_images/`, and `ui_references/` contain detection crops, game imagery, and interface assets. Game characters, artwork, logos, and trademarks remain the property of their respective owners. These materials are included for this tool's operation with the repository owner's confirmation of permission to redistribute them. The project's MIT license does not grant independent rights to third-party artwork or trademarks.

## Python dependencies

Dependencies are installed separately using `requirements.txt`; their source and binary packages are not vendored in this repository. They retain the licenses and notices in their respective distributions. Anyone distributing a compiled app must also preserve the notices and satisfy the redistribution terms for the actual bundled dependencies, including PySide6/Qt, OCR models, and native libraries.
