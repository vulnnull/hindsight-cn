import { getRequestConfig } from "next-intl/server";
import { hasLocale } from "next-intl";
import { routing } from "./routing";

// Static imports keep Turbopack/Webpack happy — dynamic template imports
// don't resolve at build time.
const loaders = {
  "zh-CN": () => import("../messages/zh-CN.json"),
  en: () => import("../messages/en.json"),
} as const;

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale;

  return {
    locale,
    messages: (await loaders[locale]()).default,
  };
});
