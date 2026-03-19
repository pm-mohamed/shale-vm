# Title

Language selection for Main Label (DE / EN)

# Description

As a shop operator, I want to select the language of the Main Label so that the label is displayed in the correct language for my target market.

Currently the Main Label is only available in German (DE). As the business is expanding to the UK market, there is a need to switch the primary label language to English (EN). The system should allow users to choose between DE and EN as the language for the Main Label output.

# Acceptance Criteria

- The user can select the language for the Main Label (DE or EN) via a configuration option in the UI
- The Main Label is generated and displayed in the selected language
- Switching from DE to EN (and vice versa) works correctly without side effects
- The selected language setting is persisted across sessions

# Technical Information

- On the upload page (`https://labelling.pm-projects.de/upload`), add a new dropdown for the exported first label page language (English or German). By default it is German — currently there is no option, it is German by default.
- After the user clicks export in the ui the first page label become english if the user choosed english from the dropdown and german if the user chooosed german