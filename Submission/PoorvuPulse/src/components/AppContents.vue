<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue';
import {GoogleGenerativeAI} from '@google/generative-ai';
import {PlayIcon} from '@heroicons/vue/24/outline';
import {Role} from '@/models/role.model';
import {useChatStore} from '@/stores/chat.store';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import {useSettingsStore} from '@/stores/settings.store';
import {FwbAlert, FwbButton, FwbSpinner} from 'flowbite-vue';
import {useAppStore} from '@/stores/app.store';

const input = ref('');
const numOfInputRows = ref(1);
const inputTextarea = ref<HTMLTextAreaElement | null>(null);
const scrollingDiv = ref<HTMLElement | null>(null);
const userScrolled = ref(false);
const pending = ref(false);

const appStore = useAppStore();
const chatStore = useChatStore();
const settingsStore = useSettingsStore();

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, {language: lang}).value;
      } catch (e) {
        console.log(e);
      }
    }
    return '';
  }
});

const isInputEnabled = computed(() => settingsStore.apiKey.length > 0 && !pending.value);
const isSendBtnEnabled = computed(
  () => input.value?.trim().length > 0 && settingsStore.apiKey.trim().length > 0
);

onMounted(() => {
  setTimeout(() => inputTextarea.value?.focus(), 100);
});

let genAI = new GoogleGenerativeAI(settingsStore.apiKey);

async function onSend() {
  pending.value = true;
  try {
    userScrolled.value = false;
    inputTextarea.value?.blur();
    await chatStore.addMessage({role: Role.user, content: input.value});
    autoScrollDown();
    sendRequestForTitle(input.value);
    input.value = '';
    await sendRequestForResponse();
  } catch (e) {
    if (e instanceof Error) {
      appStore.addError(e.message);
    }
  }
  pending.value = false;
}

async function sendRequestForTitle(message: string) {
  if (chatStore.currentChat && !chatStore.currentChat.title) {
    try {
      const model = genAI.getGenerativeModel({
        model: 'gemini-1.5-flash',
        generationConfig: {
          temperature: 0.5,
          maxOutputTokens: 1000
        }
      });
      const prompt =
        'Summarize the input as title of no more than 5 words. ' +
        `Output only the summarized title. The input is: ${message}`;
      const result = await model.generateContent(prompt);
      const response = await result.response;
      await chatStore.setCurrentChatTitle(response.text());
    } catch (e) {
      if (e instanceof Error) {
        appStore.addError(e.message);
      }
    }
  }
}

async function sendRequestForResponse() {
  if (chatStore.currentChat) {
    try {
      const currentMessage =
        chatStore.currentChat.messages[chatStore.currentChat.messages.length - 1].content;
      let contextualFeedback = '';

      try {
        const response = await fetch(
          `http://localhost:8000/feedback/?query=${encodeURIComponent(currentMessage)}`
        );
        if (response.ok) {
          const feedbackData = await response.json();
          contextualFeedback = feedbackData.combined_feedback;
        }
      } catch (error) {
        console.error('Error fetching feedback:', error);
      }

      const model = genAI.getGenerativeModel({
        model: settingsStore.model,
        generationConfig: {
          temperature: +settingsStore.temp,
          maxOutputTokens: +settingsStore.maxTokens
        }
      });

      const WRITING_CENTER_PROMPT = `You are an AI assistant for the Yale Writing Center, a division of the Yale Poorvu Center for Teaching and Learning. The Writing Center provides comprehensive writing support through one-on-one consultations with trained Writing Partners, helping Yale students at all levels develop their academic writing skills, from brainstorming and structuring arguments to refining final drafts. Writing Partners work with students across all disciplines, offering guidance on essays, research papers, creative writing, and other academic writing projects.

You have access to feedback forms submitted by students about their experiences with Writing Partners. Based on user input, you will receive semantically relevant feedback forms that provide insights into student experiences and Writing Partner effectiveness. While there may be many relevant forms in the database, you will analyze a select subset of the most pertinent feedback to provide focused insights.

[RELEVANT FEEDBACK FORMS]:
{feedback forms will appear here}

[USER INPUT]:
{user input will appear here}

Your tasks:
1. Analyze the provided feedback to offer dense and comprehensive insights about Writing Center services and effectiveness
2. Support your analysis by directly quoting relevant portions of feedback, including specific examples of student experiences and Writing Partner performance
3. Guide users toward Writing Center-relevant questions if their input is unrelated
4. Help users rephrase their input if the provided feedback forms aren't sufficiently relevant
5. Never reference feedback forms by their numerical identifiers
6. Provide balanced insights that can improve Writing Center services, including both positive feedback and constructive criticism when present
7. Only if users specifically request statistical analysis or ask about all historical feedback, explain that your insights are based on the most relevant subset of feedback examples rather than comprehensive statistical analysis
8. Write more than a simple paragraph when possible
9. Write a dedicated "Relevant Quotes" section at the end if there are more relevant quotes that may be useful to the user 

Format your responses with:
- Ample amount of direct quotes
- Clear section headers when necessary using markdown (##)
- **Bold text** for emphasis on key points
- Bullet points for listing multiple related items
- Paragraph format for detailed analysis

Remember: Users only see their input and your responses - the feedback matching process occurs automatically in the background through semantic search.`;

      const chat = model.startChat({
        history: [
          {
            role: 'model',
            parts: [{text: WRITING_CENTER_PROMPT}]
          },
          ...chatStore.currentChat.messages
            .slice(0, -1)
            .map((msg) => ({
              role: msg.role === 'user' ? 'user' : 'model',
              parts: [{text: msg.content ?? ''}]
            }))
            .filter((msg) => msg.parts[0].text !== '')
        ]
      });

      const enhancedPrompt = `[RELEVANT FEEDBACK FORMS]:\n${contextualFeedback}\n\n [USER INPUT]: ${currentMessage}`;
      console.log('Sending to Gemini:', enhancedPrompt);

      const result = await chat.sendMessageStream(enhancedPrompt);

      for await (const chunk of result.stream) {
        const chunkText = typeof chunk.text === 'function' ? chunk.text() : chunk.text;
        await chatStore.updateLastMessageStream(chunkText || '');
        autoScrollDown();
      }
    } catch (e) {
      if (e instanceof Error) {
        appStore.addError(e.message);
      }
    }
  }
}

function autoScrollDown() {
  if (scrollingDiv.value && !userScrolled.value) {
    scrollingDiv.value.scrollTop = scrollingDiv.value.scrollHeight;
  }
}

function checkIfUserScrolled() {
  if (scrollingDiv.value) {
    userScrolled.value =
      scrollingDiv.value.scrollTop + scrollingDiv.value.clientHeight !==
      scrollingDiv.value.scrollHeight;
  }
}

watch(
  () => settingsStore.apiKey,
  (newValue, oldValue) => {
    if (newValue !== oldValue) {
      genAI = new GoogleGenerativeAI(settingsStore.apiKey);
    }
  }
);
</script>

<template>
  <div class="flex flex-1 flex-col overflow-auto">
    <fwb-alert
      closable
      type="danger"
      class="mt-4 ml-4 mr-4 gap-0"
      v-for="error in appStore.errors"
      :key="error.id"
      @close="appStore.removeError(error.id)"
    >
      {{ error.message }}
    </fwb-alert>
    <main class="flex-1 p-4 overflow-auto" ref="scrollingDiv" @scroll="checkIfUserScrolled()">
      <template v-if="chatStore.currentChat">
        <template v-for="(message, index) in chatStore.currentChat.messages" :key="index">
          <template v-if="message.content && message.role === Role.user">
            <div class="flex">
              <div
                class="border-blue-600 border-2 border-solid py-2 px-3 rounded mb-4 message-content text-white"
                v-html="md.render(message.content)"
              />
            </div>
          </template>
          <template v-if="message.content && message.role === Role.assistant">
            <div class="flex">
              <div
                class="py-2 px-3 rounded mb-4 ml-5 message-content text-white"
                v-html="md.render(message.content)"
              />
            </div>
          </template>
        </template>
      </template>
    </main>
    <div class="flex w-full p-4" @focusin="numOfInputRows = 10" @focusout="numOfInputRows = 1">
      <textarea
        class="p-2 overflow-x-hidden w-full text-gray-100 bg-gray-800 rounded border border-gray-700 focus:ring-blue-500 focus:border-blue-500"
        :rows="numOfInputRows"
        :placeholder="
          pending
            ? 'Answering...'
            : settingsStore.apiKey.length === 0
              ? 'Enter your API key in settings'
              : `Chat with ${settingsStore.model}...`
        "
        ref="inputTextarea"
        v-model="input"
        @keydown.ctrl.enter="onSend"
        :disabled="!isInputEnabled"
      />
      <fwb-button
        color="default"
        @click="onSend"
        :disabled="!isSendBtnEnabled"
        class="ml-2 p-2 rounded"
      >
        <PlayIcon class="h-6 w-6" v-if="!pending"></PlayIcon>
        <fwb-spinner size="6" v-if="pending" />
      </fwb-button>
    </div>
  </div>
</template>

<style>
@import '../../node_modules/highlight.js/styles/github.css';

.message-content {
  pre:not(:last-child),
  p:not(:last-child),
  ol:not(:last-child),
  ul:not(:last-child),
  li:not(:last-child),
  table:not(:last-child),
  blockquote:not(:last-child),
  hr:not(:last-child),
  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    margin-bottom: 0.5rem;
  }

  blockquote {
    margin-left: 1rem;
    font-style: italic;
  }

  h1 {
    font-size: 1.5rem;
  }
  h2 {
    font-size: 1.25rem;
  }
  h3 {
    font-size: 1.125rem;
  }

  h1,
  h2,
  h3,
  h4,
  h5,
  h6 {
    font-weight: bold;
    margin-top: 1rem;
  }

  pre {
    margin-left: 1rem;
    background-color: rgb(31 41 55);
    color: rgb(229 231 235);
    display: table;
    border-radius: 5px;
    padding: 0 5px;
    white-space: pre-wrap;
  }

  code:not(pre code) {
    background-color: rgb(31 41 55);
    color: rgb(229 231 235);
    border-radius: 5px;
    padding: 0 1px;
  }

  a {
    color: rgb(96 165 250);
  }

  ul {
    list-style-type: disc;
    margin-left: 2rem;
  }

  ol {
    list-style-type: decimal;
    margin-left: 2rem;
  }

  td,
  th {
    border: 1px solid rgb(75 85 99);
    padding: 5px;
  }

  color: white;
}
</style>
