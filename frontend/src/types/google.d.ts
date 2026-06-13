// Minimal type declarations for the Google Identity Services (GSI) client
// script, loaded at runtime via <script src="https://accounts.google.com/gsi/client">.
// See AuthPage.tsx for usage. We only type the small surface we use.

interface GoogleCredentialResponse {
  credential: string
}

interface GoogleIdConfiguration {
  client_id: string
  callback: (response: GoogleCredentialResponse) => void
}

interface GoogleButtonConfiguration {
  theme?: 'outline' | 'filled_blue' | 'filled_black'
  size?: 'large' | 'medium' | 'small'
  width?: number
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
  locale?: string
}

interface GoogleAccountsId {
  initialize: (config: GoogleIdConfiguration) => void
  renderButton: (parent: HTMLElement, options: GoogleButtonConfiguration) => void
}

interface Window {
  google?: {
    accounts: {
      id: GoogleAccountsId
    }
  }
}
