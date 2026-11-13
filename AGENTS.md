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
- GitHub Pages is the review site. Bluehost was published via manual FTPS; unattended deployment is not configured.
- Future Bluehost publication must deploy the exact reviewed commit, only website files, and report the result.

- Everyday Favorites order: plain classic omurice (no katsu), curry, ramen. Onigiri already has its own section above; avoid repeating it in this row.

## Required asset archiving during website edits

- When the user supplies website photographs or menu source files, archive each original to Google Drive as part of the edit, without asking the user to upload it manually. This is an agent-executed workflow, not a background listener for all conversations.
- Drive root: 1J4Nq-MXNYfncs_0rTRcbMXd8IMGxNpr6. Original photos: 1D86pcqlzWuo8QX2_w6swrTBnoEcP236L. Published image versions: 1P7weZWhehgih0DFTDVsTi4Uw4_GSMYC1. Menu references: 1ixNk8QK_9R8zvOxXKx_64wna1L37Jm1R. Operating documents and asset register: 1p7BuIK5oKpw-zWFgGdhT9_1asLQmOBCB.
- Read folder metadata and the asset register before writing. Use the connected Drive upload tool with the absolute local path and verified parent folder ID. Preserve originals. Archive edited or generated published images separately.
- Asset register ID: 1UHkGHee5m1u0wvq8D78beF_x1HOxsafo. Verify parent, name and byte size after upload. Compare MD5 when exposed by metadata; otherwise download the saved file and compare bytes. Record Drive ID, URL, original filename, checksum, source-to-edited relationship, processing note and date in the register. Update the existing register by ID rather than making duplicates.
- Consult stored IDs and checksums before uploading again. Never deduplicate by filename alone. Report verified saved links. Resolve missing connections or permissions explicitly; do not claim an unverified save succeeded.
- Do not upload credentials, unrelated attachments or private backups. Do not change folder sharing without user authorization. Owner-side Drive connection must be tested separately before claiming it works from the owner's chat.
- Operating document Drive IDs: specification 1hMYcUpyGkztusk2xNLxq6uFC8nGoYPKw; owner editing guide 1Ve9bV-sRr6iM-SaftSolgowgeffO-2Ih. Keep these copies in sync when editing the repository documents, updating by ID.
