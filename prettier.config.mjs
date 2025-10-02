/**
 * @see https://prettier.io/docs/configuration
 * @type {import("prettier").Config}
 */

const config = {
  useTabs: false,
  semi: true,
  singleQuote: true,
  trailingComma: 'all',
  printWidth: 140,
  tabWidth: 2,
  bracketSpacing: true,
  arrowParens: 'always',
  plugins: ['prettier-plugin-tailwindcss'],
  tailwindFunctions: ['clsx', 'cva', 'cn', 'tv'],
};

export default config;
