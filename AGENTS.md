# Café Itadaki website

- This repository is the authoritative source. Edit index.html, styles.css and the image files.
- Keep relative asset paths for GitHub Pages and Bluehost compatibility.
- Preserve the reference design unless requested otherwise.
- Run python3 check_site.py before saving changes.
- Do not invent hours, prices, contact details or product availability.
- The hero uses hero-cafe-interior-no-customers.jpg, an AI edit of the user-supplied actual café photograph removing the two seated customers. Preserve the staff behind the counter. Original: hero-cafe-interior.jpg. The onigiri-making sample photograph remains draft content. Hours are sourced from drinks/dessert menu v28: Sun–Fri 9am–5:30pm (last order 5pm); Saturday 9am–7:30pm (last order 7pm).
- Everyday Favorites uses AI-retouched versions of café source photographs: omurice-plain-retouched.jpg, curry-retouched.jpg, ramen-retouched.jpg. Background and light were adjusted; originals remain in omurice-plain-source.jpg, pork-katsu-curry.jpg and ramen-source.jpg. The pictured ramen includes spicy miso, chashu, half an egg, corn and nori. Preserve accurate dish matching. The Featured Dish still uses the original photograph.
- Featured Dish: Pork Katsu Classic Omurice, $21.95, with chicken ketchup rice and classic ketchup, sourced from food menu r18 supplied by the user. Use the existing pork katsu omurice photograph.
- Never add credentials, unrelated menu files or local handoff archives.
- GitHub Pages is the review site. GitHub-to-Bluehost publication is configured and tested through .github/workflows/publish-bluehost.yml. The password is stored only as repository Actions secret BLUEHOST_FTP_PASSWORD.
- Future Bluehost publication must deploy the exact reviewed commit, only website files, and report the result.

- Everyday Favorites order: plain classic omurice (no katsu), curry, ramen. Onigiri already has its own section above; avoid repeating it in this row.

## Required asset archiving during website edits

- When the user supplies website photographs or menu source files, archive each original to Google Drive as part of the edit, without asking the user to upload it manually. This is an agent-executed workflow, not a background listener for all conversations.
- Locate the approved source, published image, menu and operating-document folders using the private project handoff. Do not publish private folder identifiers.
- Read folder metadata and the asset register before writing. Use the connected Drive upload tool with the absolute local path and verified parent folder ID. Preserve originals. Archive edited or generated published images separately.
- Locate the asset register in the private project handoff. Verify parent, name and byte size after upload. Compare MD5 when exposed by metadata; otherwise download the saved file and compare bytes. Record Drive ID, URL, original filename, checksum, source-to-edited relationship, processing note and date in the register. Update the existing register by ID rather than making duplicates.
- Consult stored IDs and checksums before uploading again. Never deduplicate by filename alone. Report verified saved links. Resolve missing connections or permissions explicitly; do not claim an unverified save succeeded.
- Do not upload credentials, unrelated attachments or private backups. Do not change folder sharing without user authorization. Owner-side Drive connection must be tested separately before claiming it works from the owner's chat.
- Keep private Drive copies of the specification and owner editing guide in sync, updating existing files by their verified IDs from the private project handoff.

## Shared project and production publication

- Shared-project entry: （共有PJのリンクは非公開の引き継ぎ資料を参照） Project sources include the website specification, editing guide, photo decisions and these agent rules. Project access setup and owner-side connector tests must be verified separately; do not infer access from this URL.
- Use Google Drive and GitHub connectors from the project. Keep decisions and source changes in this repository so both operators can reuse them. The local Mac folder is not the shared project's execution dependency.
- After the user explicitly approves the reviewed version for production, create or update .publication-request.json on main through the GitHub connector. Set commit to the full 40-character SHA of that reviewed main-branch version. Include a fresh request_id for repeated requests. Do not change the request file during ordinary editing.
- The request triggers the GitHub publication workflow, which packages static files, removes preview search exclusion for production, backs up existing public files to an artifact before writing, publishes through verified FTPS, and checks public bytes. Read automation/README.md before using it.
- Report success only after the matching publication run succeeds. Provide the reviewed SHA, run URL and public result. A request-file commit alone is not success. Failed runs stop or attempt recovery; inspect their actual results before taking further action.
- Production workflow test succeeded on 2026-11-13: https://github.com/konae/itadaki/actions/runs/43429582596, publishing f395cd6c2f197b27875e725788d8d3b23c9b433b. Backup artifacts are retained for 30 days. Original legacy backups remain private on the Tokyo Mac.
