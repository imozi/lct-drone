/** @type {import('stylelint').Config} */

export default {
  extends: ['stylelint-config-standard-scss', 'stylelint-config-idiomatic-order', 'stylelint-config-recommended-vue'],
  'stylelint.validate': ['css', 'scss', 'vue'],
  plugins: ['stylelint-scss'],
  ignoreFiles: ['dist/*'],
  rules: {
    'selector-class-pattern': [
      '^[a-z]([-]?[a-z0-9]+)*(__[a-z0-9]([-]?[a-z0-9]+)*)?(--[a-z0-9]([-]?[a-z0-9]+)*)?$',
      {
        resolveNestedSelectors: true,
      },
    ],
    'at-rule-no-deprecated': [
      true,
      {
        ignoreAtRules: ['tailwind', 'apply', 'variant', 'responsive', 'screen', 'custom-variant', 'theme', 'utility', 'source'],
      },
    ],
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: ['tailwind', 'apply', 'variant', 'responsive', 'screen', 'custom-variant', 'theme', 'utility', 'source'],
      },
    ],
    'scss/at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: ['tailwind', 'apply', 'variant', 'responsive', 'screen', 'custom-variant', 'theme', 'utility', 'source'],
      },
    ],
    'no-empty-source': null,
  },
};
