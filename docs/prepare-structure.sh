#!/bin/bash

echo "Preparing directory structure for testing..."

# Check if src/lib exists, if not create it
if [ ! -d "src/lib" ]; then
  echo "Creating src/lib directory..."
  mkdir -p src/lib
  
  # Create navigation.js
  cat > src/lib/navigation.js << 'NAVEOF'
export const navigation = [
  {
    title: 'Introduction',
    links: [
      { title: 'Getting started', href: '/' },
      { title: 'Installation', href: '/docs/installation' },
    ],
  },
  {
    title: 'Core concepts',
    links: [
      { title: 'Understanding agents', href: '/docs/understanding-agents' },
      {
        title: 'Collaboration patterns',
        href: '/docs/collaboration-patterns',
      },
      { title: 'Team formation', href: '/docs/team-formation' },
      {
        title: 'Agent communication',
        href: '/docs/agent-communication',
      },
      { title: 'Workspace management', href: '/docs/workspace-management' },
    ],
  },
  {
    title: 'Examples',
    links: [
      { title: 'Question answering team', href: '/docs/question-answering-team' },
      { title: 'Web research agents', href: '/docs/web-research-agents' },
      { title: 'Centralized collaboration', href: '/docs/centralized-collaboration' },
      { title: 'Decentralized collaboration', href: '/docs/decentralized-collaboration' },
      { title: 'Tool-using agents', href: '/docs/tool-using-agents' },
      {
        title: 'Multi-team orchestration',
        href: '/docs/multi-team-orchestration',
      },
    ],
  },
]
NAVEOF
  
  # Create sections.js
  cat > src/lib/sections.js << 'SECEOF'
import { slugifyWithCounter } from '@sindresorhus/slugify'

function isHeadingNode(node) {
  return (
    node.type === 'heading' &&
    [1, 2, 3, 4, 5, 6].includes(node.attributes.level) &&
    (typeof node.attributes.id === 'string' ||
      typeof node.attributes.id === 'undefined')
  )
}

function isH2Node(node) {
  return isHeadingNode(node) && node.attributes.level === 2
}

function isH3Node(node) {
  return isHeadingNode(node) && node.attributes.level === 3
}

function getNodeText(node) {
  let text = ''
  for (let child of node.children ?? []) {
    if (child.type === 'text') {
      text += child.attributes.content
    }
    text += getNodeText(child)
  }
  return text
}

export function collectSections(nodes, slugify = slugifyWithCounter()) {
  let sections = []

  for (let node of nodes) {
    if (isH2Node(node) || isH3Node(node)) {
      let title = getNodeText(node)
      if (title) {
        let id = slugify(title)
        if (isH3Node(node)) {
          if (!sections[sections.length - 1]) {
            throw new Error(
              'Cannot add `h3` to table of contents without a preceding `h2`',
            )
          }
          sections[sections.length - 1].children.push({
            ...node.attributes,
            id,
            title,
          })
        } else {
          sections.push({ ...node.attributes, id, title, children: [] })
        }
      }
    }

    sections.push(...collectSections(node.children ?? [], slugify))
  }

  return sections
}
SECEOF
  
  echo "Created necessary files in src/lib"
else
  echo "src/lib directory already exists"
fi

# Fix import issues
echo "Fixing import issues..."

# Detect OS type for sed command
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  SED_CMD="sed -i ''"
else
  # Linux and others
  SED_CMD="sed -i"
fi

# Fix @/lib imports in components
echo "Fixing @/lib imports in components..."
find src/components -type f -name "*.js*" -exec $SED_CMD 's|@/lib/|../lib/|g' {} \;

# Fix @/markdoc imports in components
echo "Fixing @/markdoc imports in components..."
find src/components -type f -name "*.js*" -exec $SED_CMD 's|@/markdoc/|../markdoc/|g' {} \;

# Fix @/components imports in markdoc
echo "Fixing @/components imports in markdoc..."
find src/markdoc -type f -name "*.js*" -exec $SED_CMD 's|@/components/|../components/|g' {} \;

# Fix @/components imports in components (for imports within the same directory)
echo "Fixing @/components imports in components..."
find src/components -type f -name "*.js*" -exec $SED_CMD 's|@/components/|./|g' {} \;

# Fix icon imports directly
echo "Fixing icon imports in the icons directory..."
for icon_file in src/components/icons/*.jsx; do
  echo "Fixing imports in $icon_file"
  # Replace the import line directly with the correct path
  $SED_CMD 's|import { DarkMode, Gradient, LightMode } from.*|import { DarkMode, Gradient, LightMode } from "../Icon"|' "$icon_file"
done

echo "Import issues fixed"

echo "Directory structure prepared for testing" 