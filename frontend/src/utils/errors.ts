export function getAuthErrorMessage(
  status: number,
  detail: string | undefined,
  mode: 'login' | 'register'
): string {
  if (status === 429) {
    return 'Too many attempts. Please wait a moment and try again.';
  }

  switch (detail) {
    case 'invalid credentials':
      return mode === 'register'
        ? 'Could not verify your Carleton credentials. Double-check your username and password.'
        : 'Incorrect username or password.';
    case 'username not found':
      return 'Incorrect username or password.';
    case 'username already exists':
      return 'That username is already taken.';
    default:
      return 'Something went wrong. Please try again.';
  }
}
