import { NextRequest, NextResponse} from "next/server";

export const config = {
  matcher: ["/", "/index"],
};

export function middleware(req: NextRequest) {}

export default middleware;
