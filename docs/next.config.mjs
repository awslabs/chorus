import withMarkdoc from '@markdoc/next.js'
import withSearch from './src/markdoc/search.mjs'
import path from 'path'
import { fileURLToPath } from 'url'

// Get the directory name equivalent in ES modules
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** @type {import('next').NextConfig} */
const nextConfig = {
  pageExtensions: ['js', 'jsx', 'md', 'ts', 'tsx'],
  output: 'export',
  // Set the base path if your site is not hosted at the root of the domain
  // basePath: '/chorus',
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
