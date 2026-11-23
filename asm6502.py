import os
import re
import shutil

import sublime
import sublime_plugin


SCOPE = "source.asm6502.dasm"
DIAGNOSTIC = r"^(.+?)(?:\(|:)([0-9]+)(?:(?:,|:)([0-9]+))?\)?:[ \t]*(.*)$"
INCLUDE = re.compile(
    r'^(?:[A-Za-z_.][\w.$]*:?[ \t]+)?[ \t]*\.?(?:include|incbin)[ \t]+'
    r'(?:"([^"]+)"|([^\s;,"]+))',
    re.IGNORECASE,
)
TOOLS_SETTINGS = "Sublime Atari 6502.sublime-settings"


class ProjectOptions:
    def __init__(self, window, view):
        self.source = view.file_name()
        project = window.project_file_name()
        self.root = os.path.dirname(project or self.source)
        self.values = view.settings().get("asm6502", {})
        if not isinstance(self.values, dict):
            raise ValueError("asm6502 must be an object in project settings.")

    def text(self, key, default=""):
        value = self.values.get(key, default)
        if not isinstance(value, str):
            raise ValueError("asm6502.{} must be a string.".format(key))
        return value

    def strings(self, key):
        value = self.values.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise ValueError("asm6502.{} must be an array of strings.".format(key))
        return value

    def path(self, name):
        return os.path.normpath(os.path.join(self.root, os.path.expanduser(name)))

    def entry(self):
        entry = self.text("entry")
        return self.path(entry) if entry else self.source

    def dasm_tool(self):
        tools = sublime.load_settings(TOOLS_SETTINGS)
        executable = self.text("dasm_path", tools.get("dasm_path", ""))
        if executable:
            executable = self.path(executable)
            if not os.path.isfile(executable):
                raise ValueError("DASM executable not found: {}".format(executable))
            return executable
        executable = shutil.which("dasm")
        if not executable:
            raise ValueError("Install DASM and add it to PATH, or set dasm_path in Sublime Atari 6502 Settings.")
        return executable

    def include_paths(self):
        return [self.path(path) for path in self.strings("include_dirs") + self.strings("binary_include_dirs")]


def dasm_command_line(options, entry, output):
    if os.path.splitext(entry)[1].lower() != ".asm" or not os.path.isfile(entry):
        raise ValueError("DASM entry must be an existing .asm file: {}".format(entry))
    if os.path.splitext(output)[1].lower() == ".asm":
        raise ValueError("The DASM output must use a ROM or binary extension.")
    args = options.strings("dasm_args")
    includes = ["-I" + path for path in options.include_paths()]
    executable = options.dasm_tool()
    os.makedirs(os.path.dirname(output), exist_ok=True)
    return [executable, entry, "-f3"] + args + includes + [
        "-R", "-E2", "-o" + output, "-l" + output + ".lst", "-s" + output + ".sym"
    ]


class Asm6502BuildCommand(sublime_plugin.WindowCommand):
    def run(self, action="assemble", kill=False, **kwargs):
        if kill:
            self.window.run_command("exec", {"kill": True})
            return

        view = self.window.active_view()
        if not view or not view.match_selector(0, SCOPE) or not view.file_name():
            sublime.status_message("Atari 6502: Save and open an assembly source file first.")
            return

        try:
            options = ProjectOptions(self.window, view)
            entry = options.entry()
            stem = os.path.splitext(os.path.basename(entry))[0]
            output = options.path(options.text("output", "build/" + stem + ".bin"))
            if action == "run":
                cmd = self.runner(options, output)
                working_dir = options.root
            else:
                cmd = dasm_command_line(options, entry, output)
                working_dir = os.path.dirname(entry)
        except (OSError, ValueError) as error:
            sublime.error_message("Atari 6502: {}".format(error))
            return

        self.window.run_command("exec", {
            "cmd": cmd,
            "working_dir": working_dir,
            "file_regex": DIAGNOSTIC if action != "run" else "",
            "kill_previous": True,
        })

    def runner(self, options, output):
        runner = options.strings("run")
        if not runner or not runner[0]:
            raise ValueError("Set asm6502.run in the project settings to run an emulator.")
        if not os.path.isfile(output):
            raise ValueError("Build the program first. Missing output file: {}".format(output))
        variables = self.window.extract_variables()
        variables.update(output=output, root=options.root)
        return sublime.expand_variables(runner, variables)


class Asm6502OpenIncludeCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return bool(self.view.file_name() and self.view.match_selector(0, SCOPE))

    def run(self, edit):
        line = self.view.substr(self.view.line(self.view.sel()[0].b))
        match = INCLUDE.match(line)
        if not match:
            sublime.status_message("Atari 6502: Place the caret on an INCLUDE or INCBIN line.")
            return

        window = self.view.window()
        try:
            options = ProjectOptions(window, self.view)
            directories = [os.path.dirname(options.entry())] + options.include_paths()
        except ValueError as error:
            sublime.error_message("Atari 6502: {}".format(error))
            return

        name = match.group(1) or match.group(2)
        for directory in directories:
            path = os.path.normpath(os.path.join(directory, name))
            if os.path.isfile(path):
                window.open_file(path)
                return
        sublime.status_message("Atari 6502: Include file not found: {}".format(name))
