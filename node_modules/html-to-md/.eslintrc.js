module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/eslint-recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  plugins: ['prettier'],
  rules: {
    'no-unused-vars': 1,
    camelcase: 0,
    'no-prototype-builtins': 0,
    'comma-dangle': 0,
    'prettier/prettier': 'error',
  },
  ignorePatterns: ['*.test.js', '*.md'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
}
