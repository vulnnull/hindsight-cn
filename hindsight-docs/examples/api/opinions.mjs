#!/usr/bin/env node
/**
 * Opinions API examples for Hindsight (Node.js)
 * Run: node examples/api/opinions.mjs
 */
import { HindsightClient } from '@vectorize-io/hindsight-client';

const HINDSIGHT_URL = process.env.HINDSIGHT_API_URL || 'http://localhost:8888';

// =============================================================================
// Setup (not shown in docs)
// =============================================================================
const client = new HindsightClient({ baseUrl: HINDSIGHT_URL });

// Seed some data about programming languages
await client.retain('my-bank', 'Python is widely used for data science and machine learning');
await client.retain('my-bank', 'Functional programming emphasizes immutability and pure functions');
await client.retain('my-bank', 'Rust has better memory safety than C++');
await client.retain('my-bank', 'C++ has a larger ecosystem and more libraries');

// =============================================================================
// Doc Examples
// =============================================================================

// [docs:opinion-form]
// Ask a question - the system may form opinions based on stored facts
const answer = await client.reflect('my-bank', 'What do you think about functional programming?');

console.log(answer.text);
// [/docs:opinion-form]


// [docs:opinion-search]
// Search for facts about a topic
const results = await client.recall('my-bank', 'programming languages');

for (const result of results.results) {
    console.log(`- ${result.text}`);
}
// [/docs:opinion-search]


// [docs:opinion-disposition]
// Create two memory banks with different dispositions
await client.createBank('open-minded', {
    name: 'Open Minded',
    disposition: { skepticism: 2, literalism: 2, empathy: 4 }
});

await client.createBank('conservative', {
    name: 'Conservative',
    disposition: { skepticism: 5, literalism: 5, empathy: 2 }
});

// Store the same facts to both
const facts = [
    'Rust has better memory safety than C++',
    'C++ has a larger ecosystem and more libraries',
    'Rust compile times are longer than C++'
];
for (const fact of facts) {
    await client.retain('open-minded', fact);
    await client.retain('conservative', fact);
}

// Ask both the same question - different dispositions lead to different responses
const q = 'Should we rewrite our C++ codebase in Rust?';

const answer1 = await client.reflect('open-minded', q);
console.log('Open-minded response:', answer1.text.slice(0, 100), '...');

const answer2 = await client.reflect('conservative', q);
console.log('Conservative response:', answer2.text.slice(0, 100), '...');
// [/docs:opinion-disposition]


// [docs:opinion-in-reflect]
const reflectAnswer = await client.reflect('my-bank', 'What language should I learn?');

console.log('Response:', reflectAnswer.text);

// See which facts influenced the response
if (reflectAnswer.based_on) {
    console.log('\nBased on these facts:');
    for (const fact of reflectAnswer.based_on) {
        console.log(`  - ${fact.text}`);
    }
}
// [/docs:opinion-in-reflect]


// =============================================================================
// Cleanup (not shown in docs)
// =============================================================================
await fetch(`${HINDSIGHT_URL}/v1/default/banks/my-bank`, { method: 'DELETE' });
await fetch(`${HINDSIGHT_URL}/v1/default/banks/open-minded`, { method: 'DELETE' });
await fetch(`${HINDSIGHT_URL}/v1/default/banks/conservative`, { method: 'DELETE' });

console.log('opinions.mjs: All examples passed');
