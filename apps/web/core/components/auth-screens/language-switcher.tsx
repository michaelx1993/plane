/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { Languages } from "lucide-react";
// plane imports
import { BILINGUAL_LANGUAGES, FALLBACK_LANGUAGE, useTranslation } from "@plane/i18n";
import type { TLanguage } from "@plane/i18n";
import { CustomSelect } from "@plane/ui";

const shortLanguageLabels: Partial<Record<TLanguage, string>> = {
  en: "EN",
  "zh-CN": "中文",
};

export function AuthLanguageSwitcher() {
  const { changeLanguage, currentLocale } = useTranslation();

  const selectedLanguage = (currentLocale || FALLBACK_LANGUAGE) as TLanguage;
  const selectedLabel = shortLanguageLabels[selectedLanguage] ?? selectedLanguage;

  const handleLanguageChange = (value: string) => {
    const language = value as TLanguage;
    if (language === selectedLanguage) return;
    changeLanguage(language);
  };

  return (
    <CustomSelect
      value={selectedLanguage}
      label={
        <span className="flex items-center gap-1.5">
          <Languages className="size-4" aria-hidden="true" />
          <span className="text-11 font-medium">{selectedLabel}</span>
        </span>
      }
      onChange={handleLanguageChange}
      buttonClassName="h-8 border-0 bg-transparent px-2 text-primary hover:bg-layer-1-hover"
      optionsClassName="min-w-32"
      placement="bottom-end"
    >
      {BILINGUAL_LANGUAGES.map((language) => (
        <CustomSelect.Option key={language.value} value={language.value}>
          {language.label}
        </CustomSelect.Option>
      ))}
    </CustomSelect>
  );
}
