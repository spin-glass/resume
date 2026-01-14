import { defineMiddleware } from "astro:middleware";

export const onRequest = defineMiddleware(async (context, next) => {
    const basicAuth = context.request.headers.get("authorization");

    if (basicAuth) {
        const authValue = basicAuth.split(" ")[1];
        const [user, pwd] = atob(authValue).split(":");

        // Environment variables should be set in your Vercel project settings
        // or in a local .env file for development.
        const validUser = import.meta.env.RESUME_USER || process.env.RESUME_USER;
        const validPass = import.meta.env.RESUME_PASS || process.env.RESUME_PASS;

        // If credentials match, proceed.
        if (validUser && validPass) {
            if (user === validUser && pwd === validPass) {
                return next();
            }
        } else {
            // If no env vars set, we skip auth
            return next();
        }
    }

    // If we have credentials configured but no auth header or invalid auth, request it.
    const validUser = import.meta.env.RESUME_USER || process.env.RESUME_USER;
    const validPass = import.meta.env.RESUME_PASS || process.env.RESUME_PASS;

    if (validUser && validPass) {
        return new Response("Auth required", {
            status: 401,
            headers: {
                "WWW-Authenticate": 'Basic realm="Secure Area"',
            },
        });
    }

    return next();
});
