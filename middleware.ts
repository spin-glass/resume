import { NextRequest, NextResponse } from "next/server";
import { withLocales } from 'nextra/locales'

export const config = {
  matcher: ["/", "/index"],
};

const middleware = function middleware(req: NextRequest) {
  const basicAuth = req.headers.get("authorization");
  const url = req.nextUrl;

  if (basicAuth) {
    const authValue = basicAuth.split(" ")[1];
    const [user, pwd] = atob(authValue).split(":");

    if (user === process.env.username && pwd === "nnAitDA5FnJ6") {
      return NextResponse.next();
    }
  }
  url.pathname = "/api/auth";

  return NextResponse.rewrite(url);
}

export default withLocales(middleware)