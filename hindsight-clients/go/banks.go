package hindsight

import (
	"context"
	"fmt"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// CreateBank creates a new memory bank or updates an existing one.
func (c *Client) CreateBank(ctx context.Context, bankID string, opts ...CreateBankOption) (*BankProfileResponse, error) {
	var cfg createBankConfig
	for _, o := range opts {
		o(&cfg)
	}

	req := &ogenapi.CreateBankRequest{}
	if cfg.name != nil {
		req.Name = ogenapi.NewOptString(*cfg.name)
	}
	if cfg.mission != nil {
		req.Mission = ogenapi.NewOptString(*cfg.mission)
	}
	if cfg.disposition != nil {
		req.Disposition = ogenapi.NewOptDispositionTraits(*cfg.disposition)
	}

	res, err := c.api.CreateOrUpdateBank(ctx, req, ogenapi.CreateOrUpdateBankParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.BankProfileResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

// GetBankProfile retrieves the profile for a memory bank.
func (c *Client) GetBankProfile(ctx context.Context, bankID string) (*BankProfileResponse, error) {
	res, err := c.api.GetBankProfile(ctx, ogenapi.GetBankProfileParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.BankProfileResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

// ListBanks returns all memory banks.
func (c *Client) ListBanks(ctx context.Context) (*BankListResponse, error) {
	res, err := c.api.ListBanks(ctx)
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.BankListResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

// DeleteBank permanently deletes a memory bank and all its data.
func (c *Client) DeleteBank(ctx context.Context, bankID string) error {
	_, err := c.api.DeleteBank(ctx, ogenapi.DeleteBankParams{
		BankID: bankID,
	})
	return err
}

// SetMission updates the mission for a memory bank.
func (c *Client) SetMission(ctx context.Context, bankID, mission string) (*BankProfileResponse, error) {
	req := &ogenapi.CreateBankRequest{
		Mission: ogenapi.NewOptString(mission),
	}

	res, err := c.api.CreateOrUpdateBank(ctx, req, ogenapi.CreateOrUpdateBankParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.BankProfileResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

// UpdateDisposition updates the personality traits for a memory bank.
func (c *Client) UpdateDisposition(ctx context.Context, bankID string, traits DispositionTraits) (*BankProfileResponse, error) {
	req := &ogenapi.UpdateDispositionRequest{
		Disposition: traits,
	}

	res, err := c.api.UpdateBankDisposition(ctx, req, ogenapi.UpdateBankDispositionParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.BankProfileResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}
