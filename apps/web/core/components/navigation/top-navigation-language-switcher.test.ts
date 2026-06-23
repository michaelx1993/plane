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

const topNavigationSource = fs.readFileSync(topNavigationPath, "utf-8");
const languageSwitcherSource = fs.readFileSync(languageSwitcherPath, "utf-8");

assert.ok(
  topNavigationSource.includes("TopNavigationLanguageSwitcher"),
  "top navigation should render the language switcher"
);
assert.ok(!topNavigationSource.includes("StarUsOnGitHubLink"), "top navigation should not render the GitHub link");
assert.ok(!topNavigationSource.includes("star-us-link"), "top navigation should not import the GitHub link");

assert.ok(
  languageSwitcherSource.includes("BILINGUAL_LANGUAGES"),
  "language switcher should use the bilingual language list"
);
assert.ok(
  languageSwitcherSource.includes("updateUserProfile({ language: value })"),
  "language switcher should persist the selected language"
);
assert.ok(
  languageSwitcherSource.includes("const { changeLanguage, currentLocale } = useTranslation()"),
  "language switcher should read the i18n changeLanguage hook"
);
assert.ok(
  languageSwitcherSource.includes("changeLanguage(value);"),
  "language switcher should update i18n immediately when the selected language changes"
);

console.log("top_navigation_language_switcher=passed");
