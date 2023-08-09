import { NextRequest, NextResponse} from "next/server";

export const config = {
  matcher: ["/", "/index"],
};

export function middleware(req: NextRequest) {
  const basicAuth = req.headers.get("authorization");
  const url = req.nextUrl

  if (basicAuth) {
    const authValue = basicAuth.split(" ")[1];
    // const [user, pwd] = Buffer.from(authValue, 'base64').toString('utf-8').split(":");
    const [user, pwd] = atob(authValue).split(':')
    if (user === process.env.username && pwd === process.env.password) {
      return NextResponse.next()
    }
  }
  url.pathname = '/api/auth'

  return NextResponse.rewrite(url)
}

// export default withLocales(middleware); withLocalesが原因
// export default middleware;
