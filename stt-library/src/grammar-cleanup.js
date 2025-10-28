/**
 * Text cleanup utilities
 * Fix grammar, add punctuation, correct context-based errors
 */

import axios from 'axios';

/**
 * Main cleanup function - routes to appropriate method
 */
export async function cleanupText(text, config) {
  const method = config.cleanupMethod || 'basic';

  switch (method) {
    case 'basic':
      return basicCleanup(text);

    case 'languagetool':
      return await languageToolCleanup(text, config);

    case 'claude':
      return await claudeCleanup(text, config);

    case 'openai':
      return await openaiCleanup(text, config);

    default:
      return basicCleanup(text);
  }
}

/**
 * Basic cleanup - FREE
 * Simple punctuation and capitalization
 */
function basicCleanup(text) {
  if (!text || text.trim().length === 0) {
    return text;
  }

  text = text.trim();

  // Capitalize first letter
  text = text.charAt(0).toUpperCase() + text.slice(1);

  // Add period at end if no punctuation
  if (!/[.!?]$/.test(text)) {
    text += '.';
  }

  // Fix common spacing issues
  text = text.replace(/\s+/g, ' '); // Multiple spaces -> single space
  text = text.replace(/\s+([.,!?;:])/g, '$1'); // Space before punctuation
  text = text.replace(/([.,!?;:])\s*([a-zA-Z])/g, '$1 $2'); // Space after punctuation

  return text;
}

/**
 * LanguageTool API - FREE (with limits)
 * Good grammar and spell checking
 */
async function languageToolCleanup(text, config) {
  try {
    const response = await axios.post(
      'https://api.languagetool.org/v2/check',
      new URLSearchParams({
        text: text,
        language: 'en-US',
        enabledOnly: 'false'
      }),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );

    let cleanedText = text;
    const matches = response.data.matches;

    // Apply suggestions (in reverse order to maintain positions)
    for (let i = matches.length - 1; i >= 0; i--) {
      const match = matches[i];
      if (match.replacements && match.replacements.length > 0) {
        const replacement = match.replacements[0].value;
        cleanedText =
          cleanedText.substring(0, match.offset) +
          replacement +
          cleanedText.substring(match.offset + match.length);
      }
    }

    return basicCleanup(cleanedText);

  } catch (error) {
    console.error('LanguageTool error:', error.message);
    return basicCleanup(text);
  }
}

/**
 * Claude API cleanup - PAID (~$0.001 per cleanup)
 * Best quality, context-aware
 */
async function claudeCleanup(text, config) {
  if (!config.claudeApiKey) {
    console.warn('Claude API key not provided, using basic cleanup');
    return basicCleanup(text);
  }

  try {
    const response = await axios.post(
      'https://api.anthropic.com/v1/messages',
      {
        model: 'claude-3-haiku-20240307',
        max_tokens: 1024,
        messages: [{
          role: 'user',
          content: `Fix grammar, add proper punctuation, and correct any misheard words based on context. Keep the original meaning intact. Only return the corrected text, nothing else.\n\nText: ${text}\n\nCorrected:`
        }]
      },
      {
        headers: {
          'x-api-key': config.claudeApiKey,
          'anthropic-version': '2023-06-01',
          'content-type': 'application/json'
        }
      }
    );

    return response.data.content[0].text.trim();

  } catch (error) {
    console.error('Claude API error:', error.response?.data || error.message);
    return basicCleanup(text);
  }
}

/**
 * OpenAI GPT cleanup - PAID (~$0.002 per cleanup)
 * Good quality, widely available
 */
async function openaiCleanup(text, config) {
  if (!config.openaiApiKey) {
    console.warn('OpenAI API key not provided, using basic cleanup');
    return basicCleanup(text);
  }

  try {
    const response = await axios.post(
      'https://api.openai.com/v1/chat/completions',
      {
        model: 'gpt-3.5-turbo',
        messages: [{
          role: 'user',
          content: `Fix grammar, add proper punctuation, and correct any misheard words based on context. Keep the original meaning intact. Only return the corrected text, nothing else.\n\nText: ${text}`
        }],
        max_tokens: 500,
        temperature: 0.3
      },
      {
        headers: {
          'Authorization': `Bearer ${config.openaiApiKey}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data.choices[0].message.content.trim();

  } catch (error) {
    console.error('OpenAI API error:', error.response?.data || error.message);
    return basicCleanup(text);
  }
}

/**
 * Custom cleanup rules
 * Add your own rules here
 */
export function customCleanup(text, rules = []) {
  let cleaned = text;

  for (const rule of rules) {
    if (rule.pattern && rule.replacement) {
      cleaned = cleaned.replace(
        new RegExp(rule.pattern, rule.flags || 'g'),
        rule.replacement
      );
    }
  }

  return cleaned;
}
