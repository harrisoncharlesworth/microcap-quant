# Deployment

Production deployment configurations for Microcap Quant.

## Files

- `DEPLOYMENT.md` - General deployment guide
- `RAILWAY_DEPLOYMENT.md` - Railway.app specific instructions
- `Dockerfile` - Container configuration
- `railway.json` - Railway service configuration

## Quick Deploy

### Railway
```bash
railway login
railway deploy
```

### Docker
```bash
docker build -t microcap-quant .
docker run -d --env-file .env microcap-quant
```
