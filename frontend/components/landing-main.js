/* Landing entry controller: bootstraps parallax hero network and interactive stage atlas */

function initLanding() {
  initLandingHero();
  initStageAtlas();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLanding);
} else {
  initLanding();
}
