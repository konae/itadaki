# Bluehost publication setup

This is the GitHub-to-Bluehost transfer component. It is not active until the workflow is committed, the repository secret is configured, and a real run succeeds. The shared ChatGPT project must also be tested separately.

The only credential required is the GitHub Actions repository secret `BLUEHOST_FTP_PASSWORD`. The FTPS host and account are fixed to the existing Itadaki hosting account in the script. Do not put the password in a file, workflow input, commit, project instruction or chat. Repository Actions write access can operate this publication workflow.

## Request a publication from the shared project

After the user reviews GitHub Pages and explicitly requests production publication, use the GitHub connector to create or update `.publication-request.json` on main with:

```json
{
  "commit": "FULL_40_CHARACTER_REVIEWED_COMMIT_SHA"
}
```

This request is distinct from editing website content. Ordinary main updates only refresh GitHub Pages. The workflow deploys the exact requested SHA, which must be an ancestor of the workflow's main commit. Publishing a previously reviewed SHA provides rollback to that version. For a repeated request, include a changed `request_id` alongside `commit` so GitHub records a new request commit.

Read the resulting workflow run and confirm success; a successful request-file write is not proof of production publication. Return the reviewed SHA, run URL, backup artifact and production verification result to the shared project.

## Transfer and recovery

1. Validate the request and check out the reviewed SHA.
2. Run the static site's validation. Package only linked static assets and production robots.txt, removing the preview noindex meta tag.
3. Connect through certificate-validated explicit FTPS and confirm the existing server prefers index.html.
4. Back up current public files. Legacy PHP files and private server settings are never included.
5. Save the backup as a GitHub Actions artifact before allowing production writes. Artifacts are retained for 30 days and are not a permanent archive.
6. Verify unchanged production state, upload temporary files, read them back, and rename assets before index.html.
7. Verify the live site's bytes over HTTPS. Restore overwritten files from the backup if publication or public verification fails. A broken FTPS connection may require manual recovery using the saved artifact. Newly added, unreferenced assets may remain after recovery.

No remote directory cleanup or deletion of WordPress files is performed. The existing .htaccess is read only; its DirectoryIndex setup was done during the original manual publication.

## Local checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3 automation/test_publish_bluehost.py
python3 automation/publish_bluehost.py prepare --output /tmp/itadaki-publication-check
```

Real `backup` and `deploy` operations require the password environment variable. Local tests use no credentials and never contact production.
