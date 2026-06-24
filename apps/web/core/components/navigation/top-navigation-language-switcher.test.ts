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

const topNavigationSource = fs.readFileSync(topNavigationPath, "utf-8");
const languageSwitcherSource = fs.readFileSync(languageSwitcherPath, "utf-8");
const authHeaderSource = fs.readFileSync(authHeaderPath, "utf-8");
const authLanguageSwitcherSource = fs.readFileSync(authLanguageSwitcherPath, "utf-8");

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

console.log("top_navigation_language_switcher=passed");
