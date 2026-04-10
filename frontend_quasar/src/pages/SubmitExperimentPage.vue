<template>
  <q-page class="flex justify-center">
    <div class="q-pa-lg tw-w-full" style="max-width: 700px">
      <h5 class="q-mb-md">Submit Experiment</h5>

      <q-banner v-if="submitStore.lastResult" class="bg-positive text-white q-mb-md" rounded>
        PR #{{ submitStore.lastResult.pr_number }} created successfully.
        <template v-slot:action>
          <q-btn flat label="Open PR" :href="submitStore.lastResult.pr_url" target="_blank" />
        </template>
      </q-banner>

      <q-banner v-if="submitStore.error" class="bg-negative text-white q-mb-md" rounded>
        {{ submitStore.error }}
      </q-banner>

      <q-form ref="formRef" @submit.prevent="onSubmit" class="q-gutter-md">
        <q-input v-model="name" label="Experiment Name" outlined :rules="[val => !!val || 'Name is required']" />

        <q-file v-model="playbookFile" label="playbook.yml" outlined accept=".yml,.yaml"
                 :rules="[val => !!val || 'Playbook file is required']">
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <q-file v-model="metadataFile" label="metadata.yml" outlined accept=".yml,.yaml"
                 :rules="[val => !!val || 'Metadata file is required']">
          <template v-slot:prepend>
            <q-icon name="attach_file" />
          </template>
        </q-file>

        <q-btn type="submit" label="Submit" color="primary" :loading="submitStore.loading" />
      </q-form>
    </div>
  </q-page>
</template>

<script lang="ts">
import { ref } from 'vue';
import { useSubmitStore } from 'src/store/submit';
import { QForm } from 'quasar';

export default {
  name: 'SubmitExperimentPage',
  setup() {
    const submitStore = useSubmitStore();
    const formRef = ref<QForm | null>(null);
    const name = ref('');
    const playbookFile = ref<File | null>(null);
    const metadataFile = ref<File | null>(null);

    async function onSubmit() {
      const valid = await formRef.value?.validate();
      if (!valid) return;
      await submitStore.submitExperiment(name.value, playbookFile.value!, metadataFile.value!);
    }

    return { submitStore, formRef, name, playbookFile, metadataFile, onSubmit };
  },
};
</script>
