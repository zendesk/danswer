"use client";

import * as Yup from "yup";
import { ZendeskIcon, TrashIcon } from "@/components/icons/icons";
import { TextFormField } from "@/components/admin/connectors/Field";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { CredentialForm } from "@/components/admin/connectors/CredentialForm";
import {
  ZendeskCredentialJson,
  ZendeskConfig,
  ConnectorIndexingStatus,
} from "@/lib/types";
import useSWR, { useSWRConfig } from "swr";
import { fetcher } from "@/lib/fetcher";
import { LoadingAnimation } from "@/components/Loading";
import { adminDeleteCredential, linkCredential } from "@/lib/credential";
import { ConnectorForm } from "@/components/admin/connectors/ConnectorForm";
import { ConnectorsTable } from "@/components/admin/connectors/table/ConnectorsTable";
import { usePopup } from "@/components/admin/connectors/Popup";
import { usePublicCredentials } from "@/lib/hooks";

const Main = () => {
  const { popup, setPopup } = usePopup();

  const { mutate } = useSWRConfig();
  const {
    data: connectorIndexingStatuses,
    isLoading: isConnectorIndexingStatusesLoading,
    error: isConnectorIndexingStatusesError,
  } = useSWR<ConnectorIndexingStatus<any, any>[]>(
    "/api/manage/admin/connector/indexing-status",
    fetcher
  );
  const {
    data: credentialsData,
    isLoading: isCredentialsLoading,
    error: isCredentialsError,
    refreshCredentials,
  } = usePublicCredentials();

  if (
    (!connectorIndexingStatuses && isConnectorIndexingStatusesLoading) ||
    (!credentialsData && isCredentialsLoading)
  ) {
    return <LoadingAnimation text="Loading" />;
  }

  if (isConnectorIndexingStatusesError || !connectorIndexingStatuses) {
    return <div>Failed to load connectors</div>;
  }

  if (isCredentialsError || !credentialsData) {
    return <div>Failed to load credentials</div>;
  }

  const ZendeskConnectorIndexingStatuses: ConnectorIndexingStatus<
    ZendeskConfig,
    ZendeskCredentialJson
  >[] = connectorIndexingStatuses.filter(
    (connectorIndexingStatus) =>
      connectorIndexingStatus.connector.source === "zendesk"
  );
  const ZendeskCredential = credentialsData.filter(
    (credential) => credential.credential_json?.zendesk_base_url
  )[0];

  return (
    <>
      {popup}
      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
        Step 1: Provide your API details
      </h2>

      {ZendeskCredential ? (
        <>
          <div className="flex mb-1 text-sm">
            <p className="my-auto">Zendesk Instance: </p>
            <p className="ml-1 italic my-auto max-w-md">
              {ZendeskCredential.credential_json?.zendesk_base_url}
            </p>
            <p className="my-auto">Username: </p>
            <p className="ml-1 italic my-auto max-w-md">
              {ZendeskCredential.credential_json?.zendesk_username}
            </p>
            <button
              className="ml-1 hover:bg-gray-700 rounded-full p-1"
              onClick={async () => {
                if (ZendeskConnectorIndexingStatuses.length > 0) {
                  setPopup({
                    type: "error",
                    message:
                      "Must delete all connectors before deleting credentials",
                  });
                  return;
                }
                await adminDeleteCredential(ZendeskCredential.id);
                refreshCredentials();
              }}
            >
              <TrashIcon />
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="text-sm">
            To get started you&apos;ll need API token details for your Zendesk
            instance. You can either use your username and password, or creating
            an API token in Admin Center. To create an API token, in Admin Center,
            click <b>Apps and integrations</b> in the sidebar, then select&nbsp;
            <b>APIs &gt; Zendesk API</b>. Create a new token and insert it here in place
            of your password, and append the string &apos;/token&apos; to your username.
            Your user account will require access to the relevant Help Centre articles to be indexed.
          </p>
          <div className="border-solid border-gray-600 border rounded-md p-6 mt-2 mb-4">
            <CredentialForm<ZendeskCredentialJson>
              formBody={
                <>
                  <TextFormField
                    name="zendesk_base_url"
                    label="Instance Base URL:"
                  />
                  <TextFormField
                    name="zendesk_username"
                    label="Username:"
                  />
                  <TextFormField
                    name="zendesk_password"
                    label="Password:"
                    type="password"
                  />
                </>
              }
              validationSchema={Yup.object().shape({
                zendesk_base_url: Yup.string().required(
                  "Please enter the base URL for your Zendesk instance"
                ),
                zendesk_username: Yup.string().required(
                  "Please enter your Zendesk Username (append /token for API token)"
                ),
                zendesk_password: Yup.string().required(
                  "Please enter your Zendesk Password or API token"
                ),
              })}
              initialValues={{
                zendesk_base_url: "",
                zendesk_username: "",
                zendesk_password: "",
              }}
              onSubmit={(isSuccess) => {
                if (isSuccess) {
                  refreshCredentials();
                  mutate("/api/manage/admin/connector/indexing-status");
                }
              }}
            />
          </div>
        </>
      )}

      {ZendeskConnectorIndexingStatuses.length > 0 && (
        <>
          <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
            Zendesk indexing status
          </h2>
          <p className="text-sm mb-2">
            The latest Help Centre article changes are fetched every
            10 minutes.
          </p>
          <div className="mb-2">
            <ConnectorsTable<ZendeskConfig, ZendeskCredentialJson>
              connectorIndexingStatuses={ZendeskConnectorIndexingStatuses}
              liveCredential={ZendeskCredential}
              getCredential={(credential) => {
                return (
                  <div>
                    <p>{credential.credential_json.zendesk_username}</p>
                  </div>
                );
              }}
              onCredentialLink={async (connectorId) => {
                if (ZendeskCredential) {
                  await linkCredential(connectorId, ZendeskCredential.id);
                  mutate("/api/manage/admin/connector/indexing-status");
                }
              }}
              onUpdate={() =>
                mutate("/api/manage/admin/connector/indexing-status")
              }
            />
          </div>
        </>
      )}

      {ZendeskCredential &&
        ZendeskConnectorIndexingStatuses.length === 0 && (
          <>
            <div className="border-solid border-gray-600 border rounded-md p-6 mt-4">
              <h2 className="font-bold mb-3">Create Connection</h2>
              <p className="text-sm mb-4">
                Press connect below to start the connection to your Zendesk
                instance.
              </p>
              <ConnectorForm<ZendeskConfig>
                nameBuilder={(values) => `ZendeskConnector`}
                source="zendesk"
                inputType="poll"
                formBody={<></>}
                validationSchema={Yup.object().shape({})}
                initialValues={{}}
                refreshFreq={10 * 60} // 10 minutes
                onSubmit={async (isSuccess, responseJson) => {
                  if (isSuccess && responseJson) {
                    await linkCredential(
                      responseJson.id,
                      ZendeskCredential.id
                    );
                    mutate("/api/manage/admin/connector/indexing-status");
                  }
                }}
              />
            </div>
          </>
        )}

      {!ZendeskCredential && (
        <>
          <p className="text-sm mb-4">
            Please provide your API details in Step 1 first! Once done with
            that, you&apos;ll be able to start the connection then see indexing
            status.
          </p>
        </>
      )}
    </>
  );
};

export default function Page() {
  return (
    <div className="mx-auto container">
      <div className="mb-4">
        <HealthCheckBanner />
      </div>
      <div className="border-solid border-gray-600 border-b mb-4 pb-2 flex">
        <ZendeskIcon size={32} />
        <h1 className="text-3xl font-bold pl-2">Zendesk</h1>
      </div>
      <Main />
    </div>
  );
}
