#!/bin/bash

echo "Testing GitHub Actions workflow locally..."

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy the docs directory to the temporary directory
echo "Copying docs directory to temporary directory..."
cp -r . $TEMP_DIR/docs

# Change to the temporary directory
cd $TEMP_DIR

# Run the prepare directory structure step
echo "Running prepare directory structure step..."
cd docs

# Install dependencies
echo "Installing dependencies..."
npm ci

# Update browserslist database
echo "Updating browserslist database..."
npx update-browserslist-db@latest

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

# Run the fix import issues step
echo "Running fix import issues step..."

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

# Run the verify imports step
echo "Running verify imports step..."
cat > verify-imports.sh << 'EOFVERIFY'
#!/bin/bash

echo "Verifying file structure and imports..."

# Check if the lib directory exists
if [ -d "src/lib" ]; then
  echo "✅ src/lib directory exists"
else
  echo "❌ src/lib directory does not exist"
  exit 1
fi

# Check if navigation.js exists
if [ -f "src/lib/navigation.js" ]; then
  echo "✅ src/lib/navigation.js exists"
else
  echo "❌ src/lib/navigation.js does not exist"
  exit 1
fi

# Check if sections.js exists
if [ -f "src/lib/sections.js" ]; then
  echo "✅ src/lib/sections.js exists"
else
  echo "❌ src/lib/sections.js does not exist"
  exit 1
fi

# Check for any remaining @/lib imports
echo "Checking for any remaining @/lib imports..."
grep -r "@/lib" src/components/ && echo "❌ Found @/lib imports in components" && exit 1 || echo "✅ No @/lib imports found in components"

# Check for any remaining @/markdoc imports
echo "Checking for any remaining @/markdoc imports..."
grep -r "@/markdoc" src/components/ && echo "❌ Found @/markdoc imports in components" && exit 1 || echo "✅ No @/markdoc imports found in components"

# Check for any remaining @/components imports
echo "Checking for any remaining @/components imports..."
grep -r "@/components" src/markdoc/ && echo "❌ Found @/components imports in markdoc" && exit 1 || echo "✅ No @/components imports found in markdoc"

# Check for any remaining @/components/Icon imports in icons directory
echo "Checking for any remaining @/components/Icon imports in icons directory..."
grep -r "@/components/Icon" src/components/icons/ && echo "❌ Found @/components/Icon imports in icons directory" && exit 1 || echo "✅ No @/components/Icon imports found in icons directory"

echo "Verification complete!"
EOFVERIFY
chmod +x verify-imports.sh
./verify-imports.sh

# Run the build step
echo "Running build step..."
npm run build

# Check if the build was successful
if [ $? -eq 0 ]; then
  echo "Build successful!"
else
  echo "Build failed. Please check the error messages above."
fi

# Clean up
echo "Cleaning up..."
cd ../..
rm -rf $TEMP_DIR
echo "Temporary directory removed"
echo "GitHub Actions workflow test completed" 