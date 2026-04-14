const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterFramework: ["<rootDir>/jest.setup.js"],
  setupFilesAfterFramework: [],
  setupFiles: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  testPathPattern: ["<rootDir>/src/__tests__/"],
};

module.exports = createJestConfig(customJestConfig);
