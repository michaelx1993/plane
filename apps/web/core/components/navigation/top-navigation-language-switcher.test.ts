/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const appRoot = path.resolve(import.meta.dirname, "../../..");
const topNavigationPath = path.join(appRoot, "ce/components/navigations/top-navigation-root.tsx");
const languageSwitcherPath = path.join(appRoot, "ce/components/navigations/language-switcher.tsx");
const authHeaderPath = path.join(appRoot, "core/components/auth-screens/header.tsx");
const authLanguageSwitcherPath = path.join(appRoot, "core/components/auth-screens/language-switcher.tsx");
const authFormHeaderPath = path.join(appRoot, "core/components/account/auth-forms/auth-header.tsx");
const authFormRootPath = path.join(appRoot, "core/components/account/auth-forms/auth-root.tsx");
const authTermsPath = path.join(appRoot, "core/components/account/terms-and-conditions.tsx");
const authFooterPath = path.join(appRoot, "core/components/auth-screens/footer.tsx");

const topNavigationSource = fs.readFileSync(topNavigationPath, "utf-8");
const languageSwitcherSource = fs.readFileSync(languageSwitcherPath, "utf-8");
const authHeaderSource = fs.readFileSync(authHeaderPath, "utf-8");
const authLanguageSwitcherSource = fs.readFileSync(authLanguageSwitcherPath, "utf-8");
const authFormHeaderSource = fs.readFileSync(authFormHeaderPath, "utf-8");
const authFormRootSource = fs.readFileSync(authFormRootPath, "utf-8");
const authTermsSource = fs.readFileSync(authTermsPath, "utf-8");
const authFooterSource = fs.readFileSync(authFooterPath, "utf-8");

assert.ok(
  topNavigationSource.includes("TopNavigationLanguageSwitcher"),
  "top navigation should render the language switcher"
);
assert.ok(
  topNavigationSource.includes('className="shrink-0 md:hidden"'),
  "top navigation should render a dedicated mobile language switcher"
);
assert.ok(
  topNavigationSource.includes('className="hidden flex-1 shrink-0 items-center justify-end gap-1 md:flex"'),
  "top navigation should keep desktop actions hidden on mobile"
);
assert.ok(!topNavigationSource.includes("StarUsOnGitHubLink"), "top navigation should not render the GitHub link");
assert.ok(!topNavigationSource.includes("star-us-link"), "top navigation should not import the GitHub link");

assert.ok(
  languageSwitcherSource.includes("BILINGUAL_LANGUAGES"),
  "language switcher should use the bilingual language list"
);
assert.ok(
  languageSwitcherSource.includes("updateUserProfile({ language })"),
  "language switcher should persist the selected language"
);
assert.ok(
  languageSwitcherSource.includes("const { changeLanguage, currentLocale } = useTranslation()"),
  "language switcher should read the i18n changeLanguage hook"
);
assert.ok(
  languageSwitcherSource.includes('import type { TLanguage } from "@plane/i18n";'),
  "language switcher should use the i18n language type"
);
assert.ok(
  languageSwitcherSource.includes("const language = value as TLanguage;"),
  "language switcher should cast CustomSelect values to the i18n language type"
);
assert.ok(
  languageSwitcherSource.includes("changeLanguage(language);"),
  "language switcher should update i18n immediately when the selected language changes"
);

const topNavPowerKPath = path.join(appRoot, "core/components/navigation/top-nav-power-k.tsx");
const topNavPowerKSource = fs.readFileSync(topNavPowerKPath, "utf-8");

assert.ok(
  topNavPowerKSource.includes("relative min-w-0"),
  "top navigation search should be allowed to shrink on mobile"
);
assert.ok(
  topNavPowerKSource.includes("w-full items-center") && topNavPowerKSource.includes("md:w-[364px]"),
  "top navigation search should only use fixed width on desktop"
);

assert.ok(authHeaderSource.includes("AuthLanguageSwitcher"), "auth header should render the language switcher");
assert.ok(
  authHeaderSource.includes("<AuthLanguageSwitcher />"),
  "auth homepage should expose the language switcher before sign in"
);
assert.ok(
  authLanguageSwitcherSource.includes("BILINGUAL_LANGUAGES"),
  "auth language switcher should use the bilingual language list"
);
assert.ok(
  authLanguageSwitcherSource.includes("changeLanguage(language);"),
  "auth language switcher should update i18n immediately"
);
assert.ok(
  !authLanguageSwitcherSource.includes("updateUserProfile"),
  "auth language switcher should not require an authenticated user profile"
);
assert.ok(
  authFormHeaderSource.includes("auth.homepage.hero.header") &&
    authFormHeaderSource.includes("auth.homepage.hero.sign_in_sub_header") &&
    authFormHeaderSource.includes("auth.homepage.hero.sign_up_sub_header"),
  "auth homepage hero copy should be driven by i18n keys"
);
assert.ok(
  !authFormHeaderSource.includes("Work in all dimensions.") &&
    !authFormHeaderSource.includes("Welcome back to Plane.") &&
    !authFormHeaderSource.includes("Create your Plane account."),
  "auth homepage hero should not hard-code English copy"
);
assert.ok(authTermsSource.includes("auth.terms.sign_in_intro"), "auth terms should use i18n keys");
assert.ok(
  !authTermsSource.includes("By signing in") && !authTermsSource.includes("By creating an account"),
  "auth terms should not hard-code English copy"
);
assert.ok(authFooterSource.includes("auth.footer.trusted_by"), "auth footer should use an i18n key");
assert.ok(!authFooterSource.includes("Join 10,000+ teams"), "auth footer should not hard-code English copy");
assert.ok(
  authFormRootSource.includes("auth.common.sign_up") && authFormRootSource.includes("auth.common.sign_in"),
  "auth OAuth action text should use i18n keys"
);
assert.ok(
  !authFormRootSource.includes('"Sign up"') && !authFormRootSource.includes('"Sign in"'),
  "auth OAuth action text should not hard-code English copy"
);

console.log("top_navigation_language_switcher=passed");
