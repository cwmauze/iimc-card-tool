# IIMC Card Tool - Public Roadmap

This roadmap outlines the planned future development for the IIMC Card Tool. Because this is an open-source, aviation life-safety application, our goals prioritize mathematical transparency, extreme accuracy, and seamless pre-flight workflow integration.

## 📌 Phase 1: Open-Source Foundation (Current)
*Focus: Establishing standard open-source protocols to encourage community trust and contributions.*
- [ ] **Add an Open-Source License:** Add an MIT or Apache 2.0 license so others can legally use and fork the code.
- [ ] **Create CONTRIBUTING.md:** Establish clear rules for how other developers or pilots can submit bug fixes, feature requests, or code contributions.
- [ ] **GitHub Issue Templates:** Standardize how users report bugs (e.g., forcing them to provide the specific FAA ID, radius, and expected vs. actual MSA).

## 📌 Phase 2: Pre-Flight Workflow & Export Enhancements
*Focus: Optimizing the tool for dispatch desks and pilot lounges to generate cards quickly before stepping to the aircraft.*
- [ ] **Batch Generation:** Allow operators to input a list of common hospital helipads or bases to generate a multi-page PDF packet of IIMC cards at once.
- [ ] **Direct EFB Integration:** Add options to "Send to ForeFlight" or "Send to Garmin Pilot" as a document payload, skipping the manual PDF save step.
- [ ] **KML/KMZ Overlay Export:** Generate a `.kml` file of the IIMC sectors and MSAs that can be imported directly into ForeFlight or Garmin Pilot as a map overlay, rather than just a static PDF reference.
- [ ] **Template Cloud Sync:** Allow operators to host a central `.json` layout template on their own servers that the tool can load automatically, ensuring all company pilots use the exact same layout.

## 📌 Phase 3: Codebase Modularization & Performance
*Focus: Breaking down the massive `index.html` file to make the codebase more maintainable for future contributors.*
- [ ] **Extract UI Logic:** Move the kneeboard generation and layout manipulation logic into a dedicated `js/pdf-generator.js`.
- [ ] **Extract Math Engine:** Move the MSA calculations, magnetic variation (WMM), and Haversine functions into a dedicated `js/calculator.js`.
- [ ] **Optimize Data Loading:** Investigate efficient streaming or IndexedDB for the 22MB `obstacles.json` to speed up initial load times on dispatch computers.

## 📌 Phase 4: Feature Expansions
*Focus: Adding highly-requested capabilities based on pilot and dispatch feedback.*
- [ ] **European/Global Airspace Support:** Expand the database fetching scripts to pull obstacle and airspace data for international regions (currently FAA/US focused).
- [ ] **Regional Area / MVA-Style Charts:** Evolve the tool to generate safe altitudes across a broader, gridded regional area (similar to an ATC Minimum Vectoring Altitude chart), rather than relying solely on a single centerpoint and radial sectors.

## 📌 Phase 5: Automated Distribution (SaaS Migration)
*Focus: Upgrading from a static Single Page App to a backend service for automated compliance and distribution.*
- [ ] **User Subscriptions:** Allow operators to define a list of coordinates (e.g., all their hospital bases) and save them to a user profile.
- [ ] **Automated Generation Engine:** Build a backend microservice (e.g., Firebase or AWS Lambda) that recalculates every saved card automatically whenever the FAA 56-day DOF cycle updates.
- [ ] **Email & Push Delivery:** Automatically email a fresh, compliant PDF packet to operators every 56 days so they never have to manually generate cards to stay compliant with new obstacles.
