import withMarkdoc from '@markdoc/next.js'

import withSearch from './src/markdoc/search.mjs'

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
}

export default withSearch(
  withMarkdoc({ schemaPath: './src/markdoc' })(nextConfig),
)
