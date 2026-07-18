export const QUICK_TIMEOUT = 15000;
export const SCRAPE_TIMEOUT = 90000;

export function isTimeout(err: unknown): boolean {
  return err instanceof DOMException && err.name === 'TimeoutError';
}

type ValidationError = { loc?: (string | number)[]; msg?: string };

export function getAuthErrorMessage(
  status: number,
  detail: string | ValidationError[] | undefined,
  mode: 'login' | 'register'
): string {
  if (status === 429) {
    return 'Too many attempts. Please wait a moment and try again.';
  }

  if (Array.isArray(detail)) {
    const emailErr = detail.find(e => e.loc?.includes('email'));
    if (emailErr) return 'Please enter a valid email address.';
    const first = detail[0]?.msg;
    return first ? `Invalid input: ${first}` : 'Something went wrong. Please try again.';
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
