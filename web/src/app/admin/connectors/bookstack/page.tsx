"use client";

import * as Yup from "yup";
import { BookstackIcon, TrashIcon } from "@/components/icons/icons";
import { TextFormField } from "@/components/admin/connectors/Field";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { CredentialForm } from "@/components/admin/connectors/CredentialForm";
import {
  BookstackCredentialJson,
  BookstackConfig,
  ConnectorIndexingStatus,
  Credential,
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

  const bookstackConnectorIndexingStatuses: ConnectorIndexingStatus<
    BookstackConfig,
    BookstackCredentialJson
  >[] = connectorIndexingStatuses.filter(
    (connectorIndexingStatus) =>
      connectorIndexingStatus.connector.source === "bookstack"
  );
  const bookstackCredential: Credential<BookstackCredentialJson> | undefined =
    credentialsData.find(
      (credential) => credential.credential_json?.bookstack_api_token_id
    );

  return (
    <>
      {popup}
      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
        Step 1: Provide your API details
      </h2>

      {bookstackCredential ? (
        <>
          <div className="flex mb-1 text-sm">
            <p className="my-auto">Existing API Token: </p>
            <p className="ml-1 italic my-auto max-w-md">
              {bookstackCredential.credential_json?.bookstack_api_token_id}
            </p>
            <button
              className="ml-1 hover:bg-gray-700 rounded-full p-1"
              onClick={async () => {
                if (bookstackConnectorIndexingStatuses.length > 0) {
                  setPopup({
                    type: "error",
                    message:
                      "Must delete all connectors before deleting credentials",
                  });
                  return;
                }
                await adminDeleteCredential(bookstackCredential.id);
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
            To get started you&apos;ll need API token details for your BookStack
            instance. You can get these by editing your (or another) user
            account in BookStack and creating a token via the &apos;API
            Tokens&apos; section at the bottom. Your user account will require
            to be assigned a BookStack role which has the &apos;Access system
            API&apos; system permission assigned.
          </p>
          <div className="border-solid border-gray-600 border rounded-md p-6 mt-2 mb-4">
            <CredentialForm<BookstackCredentialJson>
              formBody={
                <>
                  <TextFormField
                    name="bookstack_base_url"
                    label="Instance Base URL:"
                  />
                  <TextFormField
                    name="bookstack_api_token_id"
                    label="API Token ID:"
                  />
                  <TextFormField
                    name="bookstack_api_token_secret"
                    label="API Token Secret:"
                    type="password"
                  />
                </>
              }
              validationSchema={Yup.object().shape({
                bookstack_base_url: Yup.string().required(
                  "Please enter the base URL for your BookStack instance"
                ),
                bookstack_api_token_id: Yup.string().required(
                  "Please enter your BookStack API token ID"
                ),
                bookstack_api_token_secret: Yup.string().required(
                  "Please enter your BookStack API token secret"
                ),
              })}
              initialValues={{
                bookstack_base_url: "",
                bookstack_api_token_id: "",
                bookstack_api_token_secret: "",
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

      {bookstackConnectorIndexingStatuses.length > 0 && (
        <>
          <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
            BookStack indexing status
          </h2>
          <p className="text-sm mb-2">
            The latest page, chapter, book and shelf changes are fetched every
            10 minutes.
          </p>
          <div className="mb-2">
            <ConnectorsTable<BookstackConfig, BookstackCredentialJson>
              connectorIndexingStatuses={bookstackConnectorIndexingStatuses}
              liveCredential={bookstackCredential}
              getCredential={(credential) => {
                return (
                  <div>
                    <p>{credential.credential_json.bookstack_api_token_id}</p>
                  </div>
                );
              }}
              onCredentialLink={async (connectorId) => {
                if (bookstackCredential) {
                  await linkCredential(connectorId, bookstackCredential.id);
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

      {bookstackCredential &&
        bookstackConnectorIndexingStatuses.length === 0 && (
          <>
            <div className="border-solid border-gray-600 border rounded-md p-6 mt-4">
              <h2 className="font-bold mb-3">Create Connection</h2>
              <p className="text-sm mb-4">
                Press connect below to start the connection to your BookStack
                instance.
              </p>
              <ConnectorForm<BookstackConfig>
                nameBuilder={(values) => `BookStackConnector`}
                ccPairNameBuilder={(values) => `BookStackConnector`}
                source="bookstack"
                inputType="poll"
                formBody={<></>}
                validationSchema={Yup.object().shape({})}
                initialValues={{}}
                refreshFreq={10 * 60} // 10 minutes
                credentialId={bookstackCredential.id}
              />
            </div>
          </>
        )}

      {!bookstackCredential && (
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
        <BookstackIcon size={32} />
        <h1 className="text-3xl font-bold pl-2">BookStack</h1>
      </div>
      <Main />
    </div>
  );
}
