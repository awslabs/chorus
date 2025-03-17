import withMarkdoc from '@markdoc/next.js'
import withSearch from './src/markdoc/search.mjs'
import path from 'path'
import { fileURLToPath } from 'url'

// Get the directory name equivalent in ES modules
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Determine if we're building for GitHub Pages or local development
const isGithubActions = process.env.GITHUB_ACTIONS === 'true'
const basePath = isGithubActions ? '/chorus' : ''

/** @type {import('next').NextConfig} */
const nextConfig = {
  pageExtensions: ['js', 'jsx', 'md', 'ts', 'tsx'],
  output: 'export',
  // Set the base path for GitHub Pages
  basePath: basePath,
  // Set the asset prefix to match the base path
  assetPrefix: basePath,
  // Disable image optimization since it's not compatible with 'output: export'
  images: {
    unoptimized: true,
  },
  // Explicitly set the webpack configuration to resolve paths
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    };
    return config;
  },
}

export default withSearch(
  withMarkdoc({ schemaPath: './src/markdoc' })(nextConfig),
)
