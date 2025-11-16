require('dotenv').config();

console.log('=== ENVIRONMENT VARIABLES TEST ===');
console.log('SUI_PRIVATE_KEY:', process.env.SUI_PRIVATE_KEY ? 'LOADED' : 'MISSING');
console.log('PORT:', process.env.PORT);
console.log('SUI_NETWORK:', process.env.SUI_NETWORK);
console.log('AI_MODEL_PATH:', process.env.AI_MODEL_PATH);