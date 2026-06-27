/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import type { LucideIcon } from "lucide-react";

import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";

type TCenterPageMetric = {
  label: string;
  value: string;
};

type TCenterPageList = {
  title: string;
  items: string[];
};

type TCenterPageProps = {
  title: string;
  subtitle: string;
  Icon: LucideIcon;
  metrics?: TCenterPageMetric[];
  lists?: TCenterPageList[];
};

export function AgentControlCenterPage(props: TCenterPageProps) {
  const { title, subtitle, Icon, metrics = [], lists = [] } = props;

  return (
    <>
      <AppHeader
        header={
          <div className="flex items-center gap-2 px-5 py-3">
            <Icon className="size-4 text-secondary" />
            <div>
              <h1 className="text-lg font-semibold text-primary">{title}</h1>
              <p className="text-xs text-secondary">{subtitle}</p>
            </div>
          </div>
        }
      />
      <ContentWrapper>
        <PageHead title={title} />
        <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 p-6">
          {metrics.length > 0 && (
            <section className="grid gap-3 md:grid-cols-4">
              {metrics.map((metric) => (
                <div key={metric.label} className="rounded border border-subtle bg-surface-1 p-4">
                  <div className="text-xs font-medium text-secondary">{metric.label}</div>
                  <div className="text-2xl mt-2 font-semibold text-primary">{metric.value}</div>
                </div>
              ))}
            </section>
          )}
          {lists.length > 0 && (
            <section className="grid gap-4 lg:grid-cols-2">
              {lists.map((list) => (
                <div key={list.title} className="rounded border border-subtle bg-surface-1 p-4">
                  <h2 className="text-sm font-semibold text-primary">{list.title}</h2>
                  <div className="mt-3 flex flex-col divide-y divide-subtle">
                    {list.items.map((item) => (
                      <div key={item} className="text-sm py-2 text-secondary">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </section>
          )}
        </main>
      </ContentWrapper>
    </>
  );
}
