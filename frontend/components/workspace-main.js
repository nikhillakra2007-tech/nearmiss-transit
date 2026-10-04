/* Workspace entry controller: connects decoupled components, bootstraps state, and runs cycles */

async function initWorkspace() {
  const handleOpenPattern = (patternId) => {
    if (typeof window.switchSection === "function") {
      window.switchSection("detail");
    }
    openPattern(patternId);
    const h = $("h-detail");
    if (h) {
      h.focus({ preventScroll: true });
    }
  };

  const refreshAll = async () => {
    await Promise.all([
      refreshStatus(),
      refreshOps(),
      refreshPatterns(handleOpenPattern),
      refreshNearMisses(handleOpenPattern),
      refreshResilience(handleOpenPattern),
      refreshForecast(handleOpenPattern),
    ]);
  };

  // Wire up manual ingestion trigger
  initIngestionTrigger(refreshAll);

  // Initialize workspace navigation
  initWorkspaceNav();

  // Initial load
  await refreshAll();

  // Auto-refresh telemetry every 30 seconds
  setInterval(() => {
    refreshStatus();
    refreshOps();
  }, 30000);
}

// Bootstrap on DOM ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initWorkspace);
} else {
  initWorkspace();
}
