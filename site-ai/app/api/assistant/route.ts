import OpenAI from 'openai';

export const runtime = 'nodejs';

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const systemPrompt = `
Tu es un assistant vendeur pour une entreprise canadienne de moteurs usagés.
Ton objectif est de qualifier le client rapidement et poliment.

Tu dois obtenir les informations suivantes :
- nom du client si possible
- téléphone si possible
- année du véhicule
- marque
- modèle
- moteur/litrage
- VIN complet ou 8e caractère du VIN
- ville de livraison
- livraison seulement ou installation aussi
- budget approximatif
- urgence

Règles :
- Réponds en français canadien simple.
- Pose une seule question à la fois.
- Ne donne jamais un prix inventé.
- Si le client demande un prix, dis que tu dois d'abord confirmer compatibilité, kilométrage disponible et livraison.
- Si les informations essentielles sont manquantes, demande la prochaine information la plus importante.
- Si assez d'informations sont présentes, résume la demande et dis qu'une soumission peut être préparée.
- Ton ton doit être vendeur, professionnel, direct et rassurant.
`;

function fallbackAssistant(messages: ChatMessage[]) {
  const text = messages.map((m) => m.content).join(' ').toLowerCase();

  if (!/\b(19|20)\d{2}\b/.test(text)) {
    return 'Parfait. Pour commencer, quelle est l’année du véhicule?';
  }
  if (!/(ford|chevrolet|chevy|gmc|dodge|ram|honda|toyota|kia|hyundai|nissan|mazda|jeep|bmw|audi|volkswagen|vw)/i.test(text)) {
    return 'Merci. Quelle est la marque du véhicule?';
  }
  if (!/(vin|8e|8eme|8 ème|huitieme|huitième)/i.test(text)) {
    return 'Avez-vous le VIN complet ou au moins le 8e caractère du VIN pour confirmer le bon moteur?';
  }
  if (!/(montreal|montréal|quebec|québec|laval|gatineau|toronto|ottawa|sherbrooke|trois-rivieres|trois-rivières)/i.test(text)) {
    return 'Dans quelle ville doit-on livrer le moteur?';
  }
  return 'Parfait, j’ai assez d’informations pour préparer la demande. Voulez-vous une livraison seulement ou aussi une installation avec un garage partenaire?';
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const messages = (body.messages || []) as ChatMessage[];

    if (!process.env.OPENAI_API_KEY) {
      return Response.json({
        reply: fallbackAssistant(messages),
        mode: 'fallback',
      });
    }

    const conversation = messages
      .slice(-12)
      .map((message) => `${message.role === 'user' ? 'Client' : 'Assistant'}: ${message.content}`)
      .join('\n');

    const response = await openai.responses.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      input: `${systemPrompt}\n\nConversation actuelle:\n${conversation}\n\nRéponds maintenant au client.`,
      temperature: 0.4,
      max_output_tokens: 260,
    });

    return Response.json({
      reply: response.output_text || fallbackAssistant(messages),
      mode: 'openai',
    });
  } catch (error) {
    console.error('Assistant API error:', error);
    return Response.json(
      { reply: 'Désolé, l’assistant a eu un problème. Pouvez-vous me donner l’année, le modèle et le VIN du véhicule?', mode: 'error' },
      { status: 500 }
    );
  }
}
