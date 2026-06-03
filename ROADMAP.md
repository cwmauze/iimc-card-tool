# IIMC Card Tool - Public Roadmap

This roadmap outlines the planned future development for the IIMC Card Tool. Because this is an open-source, aviation life-safety application, our goals prioritize absolute reliability, offline availability, and mathematical transparency.

## 📌 Phase 1: Open-Source Foundation (Current)
*Focus: Establishing standard open-source protocols to encourage community trust and contributions.*
- [ ] **Add an Open-Source License:** Add an MIT or Apache 2.0 license so others can legally use and fork the code.
- [ ] **Create CONTRIBUTING.md:** Establish clear rules for how other developers or pilots can submit bug fixes, feature requests, or code contributions.
- [ ] **GitHub Issue Templates:** Standardize how users report bugs (e.g., forcing them to provide the specific FAA ID, radius, and expected vs. actual MSA).

## 📌 Phase 2: True Offline Reliability (PWA)
*Focus: Ensuring the tool is 100% reliable in the cockpit without a cellular connection.*
- [ ] **Implement a Service Worker:** Upgrade the site to a Progressive Web App (PWA). This will force the browser to locally cache `index.html`, all JavaScript, and the heavy JSON data files permanently.
- [ ] **Install to Home Screen:** Configure the `manifest.json` so pilots can install the tool directly to their iPad/tablet home screen as a standalone application.
- [ ] **Cache Versioning:** Build a mechanism to gracefully update the local offline cache whenever the weekly GitHub Actions push new FAA data to the live site.

## 📌 Phase 3: Codebase Modularization & Performance
*Focus: Breaking down the massive `index.html` file to make the codebase more maintainable for future contributors.*
- [ ] **Extract UI Logic:** Move the kneeboard generation and layout manipulation logic into a dedicated `js/pdf-generator.js`.
- [ ] **Extract Math Engine:** Move the MSA calculations, magnetic variation (WMM), and Haversine functions into a dedicated `js/calculator.js`.
- [ ] **Optimize Data Loading:** Investigate IndexedDB for storing the 22MB `obstacles.json` to reduce browser memory footprint on older iPads.

## 📌 Phase 4: Feature Expansions
*Focus: Adding highly-requested capabilities based on pilot feedback.*
- [ ] **European/Global Airspace Support:** Expand the database fetching scripts to pull obstacle and airspace data for international regions (currently FAA/US focused).
- [ ] **Night Mode / NVG Compliance:** Add a strict red/black high-contrast night mode for use under Night Vision Goggles.
- [ ] **Custom Obstacle Overrides:** Allow pilots to manually input temporary obstacles (e.g., temporary cranes) that are not yet published in the FAA DOF.
