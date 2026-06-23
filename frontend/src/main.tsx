import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { Toaster } from "sonner";
import { getRouter } from "./router";

const router = getRouter();

import React, { Component, ErrorInfo, ReactNode } from "react";

class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // TODO: Dispatch to observability platform like Sentry or Datadog
    window.dispatchEvent(new CustomEvent("apm-error", { detail: { error, errorInfo } }));
    console.error("Uncaught error logged to APM mechanism.");
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-foreground">
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 max-w-md">
            <h1 className="mb-2 text-xl font-semibold text-red-500">Something went wrong</h1>
            <p className="text-sm text-muted-foreground mb-4">
              The application encountered an unexpected error. Please contact support if the issue
              persists.
            </p>
            <button
              onClick={() => {
                localStorage.clear();
                sessionStorage.clear();
                window.location.reload();
              }}
              className="mt-4 rounded bg-red-500 px-4 py-2 text-sm text-white hover:bg-red-600 transition-colors"
            >
              Clear Cache & Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = createRoot(rootElement);
  root.render(
    <StrictMode>
      <ErrorBoundary>
        <RouterProvider router={router} />
        <Toaster richColors position="top-center" />
      </ErrorBoundary>
    </StrictMode>,
  );
}
