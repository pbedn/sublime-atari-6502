# Sublime Atari 6502

A Sublime Text 4 package for Atari 2600, 5200, and 7800 assembly development with DASM. It highlights 6502 assembly in `.asm` files and provides mnemonic completion, directive snippets, symbol navigation, and clickable build diagnostics.

## Install

Requires Sublime Text 4. The syntax, completions, and navigation work as soon as the package is installed. Builds use a separately installed assembler.

1. In Sublime Text, choose **Preferences → Browse Packages**.
2. Go up one directory and copy `Sublime Atari 6502.sublime-package` into **Installed Packages**. To install from source, clone or extract the repository directly into a folder named `Sublime Atari 6502` under **Packages**.
3. Install [DASM](https://dasm-assembler.github.io/). Put it on `PATH` and restart Sublime Text, or set its path in the package preferences.

If you installed the earlier `6502 Assembly` package manually, remove that installation and copy any personal `dasm_path` value into the new package settings.

Only `.asm` files get the syntax automatically. To highlight an include file with another extension, choose **Atari 6502 (DASM)** in the status bar syntax menu.

## Package preferences

**Preferences: Sublime Atari 6502 Settings** in the Command Palette opens the package preferences. The only setting there is `dasm_path`. Set it to the full path of the DASM executable, or leave it blank to use `PATH`. You can build a single `.asm` file with this setup alone.

## Build and run

Open a saved `.asm` file and run **Build**. Sublime Text selects **Atari 6502 (DASM)** automatically when **Tools → Build System → Automatic** is active. You can also select **Atari 6502 (DASM)** directly.

By default, DASM assembles the active file and its includes into `build/<entry-stem>.bin` and writes the listing and symbols alongside it as `<entry-stem>.bin.lst` and `<entry-stem>.bin.sym`. Click a diagnostic in the build panel or use **Tools → Build Results → Next Result** to jump to its location.

| Console | Build considerations |
| --- | --- |
| Atari 2600 | Assemble the cartridge source and load the resulting raw `.bin` in Stella. |
| Atari 5200 | Assemble DASM-format source with the cartridge layout and vectors required by your project. Use the image format and cartridge type your emulator or hardware expects. |
| Atari 7800 | Assemble DASM-format source for your cartridge layout. For an `.a78` image, include the A78 header in the source or add it with your existing tooling. Set `output` to match the format the source actually emits. |

DASM follows the CPU, origins, and data declared by the source. Cartridge headers, bank switching, and 7800 hardware signing are handled by the source or your cartridge tooling. See the [DASM manual](https://github.com/dasm-assembler/dasm/blob/master/docs/dasm.txt) and the [A78 header specification](https://7800.8bitdev.org/index.php/A78_Header_Specification).

## Optional project settings

Use a `.sublime-project` file when you want to build a fixed entry point while editing several files, add include directories, or launch an emulator. In Sublime Text, save a project with **Project → Save Project As…**, then open it with **Project → Edit Project**. Add your options under `settings.asm6502`.

This example always builds `main.asm` into `build/game.bin`. With Stella on `PATH`, **Atari 6502: Run Program** opens the last built ROM.

```json
{
    "folders": [{"path": ".", "folder_exclude_patterns": ["build"]}],
    "settings": {
        "asm6502": {
            "entry": "main.asm",
            "output": "build/game.bin",
            "run": ["stella", "$output"]
        }
    }
}
```

All keys below are optional. Relative paths in a project are resolved from the directory containing the `.sublime-project` file. For a standalone build, the output directory is relative to the active source file.

| Setting | Purpose |
| --- | --- |
| `dasm_path` | Override the User settings or `PATH` for this project. |
| `entry` | DASM entry point. Defaults to the active `.asm` file. |
| `dasm_args` | Extra DASM arguments, one string per argument. The output format defaults to `-f3` for raw binary. |
| `output` | Program or ROM path. Defaults to `build/<entry-stem>.bin`. |
| `include_dirs` | Additional assembly include directories. |
| `binary_include_dirs` | Additional binary include directories. DASM shares its include search path for both source and binary includes. |
| `run` | Emulator executable and arguments as an array, for example `["stella", "$output"]`. Use `$output` for the built ROM and `$root` for the project directory. |
