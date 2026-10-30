export interface TokenClaims {
  exp?: number;
  demo?: boolean;
}

export function readTokenClaims(token: string): TokenClaims | null {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/')));
  } catch {
    return null;
  }
}

export function isTokenUsable(claims: TokenClaims | null): boolean {
  return typeof claims?.exp === 'number' && claims.exp * 1000 > Date.now();
}
