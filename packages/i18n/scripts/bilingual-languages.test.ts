/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import assert from "node:assert/strict";
import { BILINGUAL_LANGUAGES, SUPPORTED_LANGUAGES } from "../src/constants/language.js";
import { loadLocale } from "./lib/locale-io.js";

const bilingualValues = BILINGUAL_LANGUAGES.map((language) => language.value);

assert.deepEqual(bilingualValues, ["en", "zh-CN"]);

for (const language of BILINGUAL_LANGUAGES) {
  assert.ok(
    SUPPORTED_LANGUAGES.some((supportedLanguage) => supportedLanguage.value === language.value),
    `${language.value} must stay in SUPPORTED_LANGUAGES`
  );
}

const english = loadLocale("en");
const simplifiedChinese = loadLocale("zh-CN");

assert.deepEqual(
  simplifiedChinese.namespaces.map((namespace) => namespace.name).toSorted(),
  english.namespaces.map((namespace) => namespace.name).toSorted()
);
assert.equal(simplifiedChinese.allKeys.size, english.allKeys.size);

for (const key of english.allKeys) {
  assert.ok(simplifiedChinese.allKeys.has(key), `zh-CN is missing locale key: ${key}`);
}

for (const key of simplifiedChinese.allKeys) {
  assert.ok(english.allKeys.has(key), `zh-CN has stale locale key: ${key}`);
}

console.log("bilingual_languages=passed");
