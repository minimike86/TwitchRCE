class Utils:

    @staticmethod
    def redact_secret_string(secret_string: str, visible_chars: int = 4) -> str:
        """
        Redact a secret_string, showing only the first and last few characters.

        Parameters:
        - token (str): The token to redact.
        - visible_chars (int): The number of characters to show at the start and end.

        Returns:
        - str: The redacted secret_string, e.g., "abcd****wxyz".
        """
        if len(secret_string) <= visible_chars * 2:
            # If token is too short, fully redact it
            return "*" * len(secret_string)

        # Keep the first and last `visible_chars` characters, redact the rest
        return (
            f"{secret_string[:visible_chars]}"
            f"{'*' * (len(secret_string) - visible_chars * 2)}"
            f"{secret_string[-visible_chars:]}"
        )
