# Deployment

## Local

```bash
python3 app.py
```

Open http://localhost:8000.

## Render

GitHub Pages can host only the static frontend; it cannot execute `app.py` or provide the `/api/*` endpoints. Deploy the repository as a Render Web Service using the included `render.yaml` file. Render will run:

```bash
python3 app.py
```

After deployment, open the Render service URL. Do not use the GitHub Pages URL for the full application.

The service binds to `0.0.0.0` through the `QPATH_HOST` environment variable and uses Render's `PORT` environment variable automatically.
