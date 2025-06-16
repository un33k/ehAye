"""CLI-specific exception classes."""

from typing import Any, Dict, List, Optional

from .base import EhAyeError


class CLIError(EhAyeError):
    """Base exception for CLI-related errors."""
    
    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        exit_code: int = 1,
        code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message, code, context, cause)
        self.command = command
        self.exit_code = exit_code
        
        if command:
            self.context["command"] = command
        self.context["exit_code"] = exit_code


class CommandError(CLIError):
    """Raised when a CLI command fails."""
    
    def __init__(
        self,
        command: str,
        message: str,
        exit_code: int = 1,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if stdout:
            context["stdout"] = stdout[:1000]  # Truncate long output
        if stderr:
            context["stderr"] = stderr[:1000]
        
        super().__init__(
            message,
            command=command,
            exit_code=exit_code,
            context=context,
            cause=cause
        )


class ArgumentError(CLIError):
    """Raised when CLI arguments are invalid."""
    
    def __init__(
        self,
        message: str,
        argument_name: Optional[str] = None,
        argument_value: Optional[str] = None,
        valid_values: Optional[List[str]] = None,
        command: Optional[str] = None
    ):
        context = {}
        if argument_name:
            context["argument_name"] = argument_name
        if argument_value:
            context["argument_value"] = argument_value
        if valid_values:
            context["valid_values"] = valid_values
        
        super().__init__(
            message,
            command=command,
            context=context
        )


class ValidationError(CLIError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[str] = None,
        validation_rule: Optional[str] = None,
        command: Optional[str] = None
    ):
        context = {}
        if field_name:
            context["field_name"] = field_name
        if field_value:
            context["field_value"] = field_value
        if validation_rule:
            context["validation_rule"] = validation_rule
        
        super().__init__(
            message,
            command=command,
            context=context
        )


class MissingArgumentError(ArgumentError):
    """Raised when required arguments are missing."""
    
    def __init__(
        self,
        argument_name: str,
        command: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        message = f"Missing required argument: {argument_name}"
        context = {}
        if suggestions:
            context["suggestions"] = suggestions
        
        super().__init__(
            message,
            argument_name=argument_name,
            command=command,
            context=context
        )


class InvalidArgumentError(ArgumentError):
    """Raised when argument values are invalid."""
    
    def __init__(
        self,
        argument_name: str,
        argument_value: str,
        reason: str,
        valid_values: Optional[List[str]] = None,
        command: Optional[str] = None
    ):
        message = f"Invalid value for {argument_name}: {reason}"
        
        super().__init__(
            message,
            argument_name=argument_name,
            argument_value=argument_value,
            valid_values=valid_values,
            command=command
        )


class ConflictingArgumentsError(ArgumentError):
    """Raised when conflicting arguments are provided."""
    
    def __init__(
        self,
        conflicting_args: List[str],
        command: Optional[str] = None,
        resolution_hint: Optional[str] = None
    ):
        args_str = ", ".join(conflicting_args)
        message = f"Conflicting arguments: {args_str}"
        
        context = {
            "conflicting_args": conflicting_args,
        }
        if resolution_hint:
            context["resolution_hint"] = resolution_hint
        
        super().__init__(
            message,
            command=command,
            context=context
        )


class InteractiveInputError(CLIError):
    """Raised when interactive input fails."""
    
    def __init__(
        self,
        message: str,
        input_type: str,
        max_attempts: Optional[int] = None,
        attempts_made: Optional[int] = None,
        cause: Optional[Exception] = None
    ):
        context = {
            "input_type": input_type,
        }
        if max_attempts is not None:
            context["max_attempts"] = max_attempts
        if attempts_made is not None:
            context["attempts_made"] = attempts_made
        
        super().__init__(
            message,
            context=context,
            cause=cause
        )


class OutputFormattingError(CLIError):
    """Raised when output formatting fails."""
    
    def __init__(
        self,
        message: str,
        formatter_type: str,
        data_type: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        context = {
            "formatter_type": formatter_type,
        }
        if data_type:
            context["data_type"] = data_type
        
        super().__init__(
            message,
            context=context,
            cause=cause
        )


class HelpRequestError(CLIError):
    """Special exception for help requests (not really an error)."""
    
    def __init__(self, command: Optional[str] = None, help_text: Optional[str] = None):
        message = "Help requested"
        context = {}
        if help_text:
            context["help_text"] = help_text
        
        super().__init__(
            message,
            command=command,
            exit_code=0,  # Help is not an error
            context=context
        )


class KeyboardInterruptError(CLIError):
    """Raised when user interrupts with Ctrl+C."""
    
    def __init__(self, command: Optional[str] = None, cleanup_needed: bool = False):
        message = "Operation interrupted by user"
        context = {
            "cleanup_needed": cleanup_needed,
        }
        
        super().__init__(
            message,
            command=command,
            exit_code=130,  # Standard exit code for SIGINT
            context=context
        )


class ConfigurationCLIError(CLIError):
    """Raised when CLI configuration is invalid."""
    
    def __init__(
        self,
        message: str,
        config_file: Optional[str] = None,
        config_section: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        context = {}
        if config_file:
            context["config_file"] = config_file
        if config_section:
            context["config_section"] = config_section
        
        super().__init__(
            message,
            context=context,
            cause=cause
        )