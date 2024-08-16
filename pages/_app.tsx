import 'tailwindcss/tailwind.css';
import { SessionProvider } from 'next-auth/react';
import type { AppProps } from 'next/app';

function Resume({ Component, pageProps }: AppProps) {
  const { session, ...rest } = pageProps;

  return (
    <SessionProvider session={session}>
      <Component {...rest} />
    </SessionProvider>
  );
}

export default Resume;
