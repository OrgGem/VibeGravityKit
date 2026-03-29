/**
 * Download and extract GravityKit assets from GitHub.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { createGunzip } = require('zlib');
const { REPO_OWNER, REPO_NAME, VERSION } = require('./constants');

/**
 * Follow redirects and download a URL to a file.
 * @param {string} url
 * @param {string} dest
 * @param {number} maxRedirects
 * @returns {Promise<void>}
 */
function downloadFile(url, dest, maxRedirects = 5) {
  return new Promise((resolve, reject) => {
    if (maxRedirects <= 0) return reject(new Error('Too many redirects'));

    const client = url.startsWith('https') ? https : http;
    client.get(url, { headers: { 'User-Agent': 'gkt-npx' } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        // Follow redirect
        return downloadFile(res.headers.location, dest, maxRedirects - 1)
          .then(resolve)
          .catch(reject);
      }

      if (res.statusCode !== 200) {
        return reject(new Error(`Download failed: HTTP ${res.statusCode}`));
      }

      const stream = fs.createWriteStream(dest);
      res.pipe(stream);
      stream.on('finish', () => {
        stream.close();
        resolve();
      });
      stream.on('error', reject);
    }).on('error', reject);
  });
}

/**
 * Extract a .tar.gz file using Node.js built-in zlib + tar parsing.
 * We use a minimal tar extraction to avoid external dependencies.
 *
 * @param {string} tarGzPath Path to .tar.gz file
 * @param {string} destDir   Destination directory
 * @param {string} stripPrefix  Strip this prefix from paths in the tarball
 * @returns {Promise<void>}
 */
function extractTarGz(tarGzPath, destDir, stripPrefix = '') {
  return new Promise((resolve, reject) => {
    const input = fs.createReadStream(tarGzPath);
    const gunzip = createGunzip();
    const chunks = [];

    input.pipe(gunzip);

    gunzip.on('data', (chunk) => chunks.push(chunk));
    gunzip.on('end', () => {
      try {
        const buffer = Buffer.concat(chunks);
        extractTar(buffer, destDir, stripPrefix);
        resolve();
      } catch (err) {
        reject(err);
      }
    });
    gunzip.on('error', reject);
    input.on('error', reject);
  });
}

/**
 * Minimal tar extractor — handles standard USTAR format.
 */
function extractTar(buffer, destDir, stripPrefix) {
  let offset = 0;

  while (offset < buffer.length - 512) {
    // Read header (512 bytes)
    const header = buffer.slice(offset, offset + 512);

    // Check for zero block (end of archive)
    if (header.every((b) => b === 0)) break;

    // Parse file name
    let name = header.slice(0, 100).toString('utf8').replace(/\0/g, '');

    // USTAR prefix field
    const prefix = header.slice(345, 500).toString('utf8').replace(/\0/g, '');
    if (prefix) name = prefix + '/' + name;

    // Parse size (octal)
    const sizeStr = header.slice(124, 136).toString('utf8').replace(/\0/g, '').trim();
    const size = parseInt(sizeStr, 8) || 0;

    // Parse type ('0' or '' = file, '5' = directory)
    const type = String.fromCharCode(header[156]);

    offset += 512; // Move past header

    // Strip prefix from tar path (e.g. "VibeGravityKit-3.3.0/")
    let relPath = name;
    if (stripPrefix && relPath.startsWith(stripPrefix)) {
      relPath = relPath.slice(stripPrefix.length);
    }

    // Skip empty paths
    if (!relPath || relPath === '/') {
      offset += Math.ceil(size / 512) * 512;
      continue;
    }

    const fullPath = path.join(destDir, relPath);

    if (type === '5' || name.endsWith('/')) {
      // Directory
      fs.mkdirSync(fullPath, { recursive: true });
    } else if (type === '0' || type === '' || type === '\0') {
      // Regular file
      fs.mkdirSync(path.dirname(fullPath), { recursive: true });
      const fileData = buffer.slice(offset, offset + size);
      fs.writeFileSync(fullPath, fileData);
    }

    // Advance past file data (padded to 512-byte blocks)
    offset += Math.ceil(size / 512) * 512;
  }
}

/**
 * Download and extract the GravityKit source from a specific version tag.
 *
 * @param {string} version  Tag version (e.g. "3.3.0")
 * @param {string} tmpDir   Temp directory for download
 * @returns {Promise<string>} Path to the extracted source root
 */
async function downloadRelease(version, tmpDir) {
  const tag = `v${version}`;
  const url = `https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/tags/${tag}.tar.gz`;
  const tarPath = path.join(tmpDir, `${REPO_NAME}-${tag}.tar.gz`);
  const extractDir = path.join(tmpDir, 'extracted');

  fs.mkdirSync(extractDir, { recursive: true });

  console.log(`⬇️  Downloading GravityKit ${tag} from GitHub...`);
  await downloadFile(url, tarPath);

  console.log(`📦 Extracting...`);
  const stripPrefix = `${REPO_NAME}-${version}/`;
  await extractTarGz(tarPath, extractDir, stripPrefix);

  // Clean up tarball
  fs.unlinkSync(tarPath);

  return extractDir;
}

module.exports = { downloadFile, extractTarGz, downloadRelease };
